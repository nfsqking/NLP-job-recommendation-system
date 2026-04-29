# -*- coding: utf-8 -*-
"""智联招聘岗位爬虫模块

该模块用于从 www.zhaopin.com 网站爬取岗位信息。
支持独立运行和被 Flask 应用调用。
"""

import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Optional, List

import parsel
import requests
import urllib3
from requests.adapters import HTTPAdapter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


CONFIG = {
    'EDGE_DRIVER_PATH': r'E:\edgedriver_win64\msedgedriver.exe',
    'BASE_URL': 'https://www.zhaopin.com/citymap/',
    'DETAIL_URL': 'https://www.zhaopin.com/jobdetail/{job_id}.htm?refcode=4019&srccode=401903&preactionid=c3225bd3-89bf-4d81-9f39-28152903b63a',
    'DB_NAME': 'jobs.db',
    'WAIT_TIMEOUT': 20,
    'PAGE_LOAD_DELAY': 1,
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
    'JOBS_PER_PAGE': 20,
}


@dataclass
class JobInfo:
    """岗位信息数据类"""
    job_id: str
    job_name: str
    job_salary: str
    location: str
    experience: str
    education: str
    job_description: str
    company_name: str
    industry: str
    company_type: str
    company_size: str
    detail_url: str


class DatabaseManager:
    """数据库管理类，负责岗位数据的存储。"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[object] = None

    def connect(self) -> None:
        """连接数据库"""
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()
        logger.info(f"数据库连接成功: {self.db_path}")

    def _create_table(self) -> None:
        """创建数据表"""
        import sqlite3
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                job_name TEXT,
                job_salary TEXT,
                location TEXT,
                experience TEXT,
                education TEXT,
                job_description TEXT,
                company_name TEXT,
                industry TEXT,
                company_type TEXT,
                company_size TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_job(self, job: JobInfo) -> None:
        """保存岗位信息"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO jobs 
            (job_id, job_name, job_salary, location, experience, education,
             job_description, company_name, industry, company_type, company_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job.job_id, job.job_name, job.job_salary, job.location,
            job.experience, job.education, job.job_description,
            job.company_name, job.industry, job.company_type, job.company_size
        ))
        self.conn.commit()

    def close(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")


class ZhilianSpider:
    """智联招聘岗位爬虫类。"""

    CONFIG = CONFIG
    SELECTORS = {
        'job_name': '.summary-planes__title span::text',
        'job_salary': 'span.summary-planes__salary::text',
        'detail_info': 'ul.summary-planes__info li::text',
        'job_description': '//*[@id="root"]/div[2]/div/section/div[2]/div/div[2]/div[2]',
        'company_name': 'span.company-summary__name a.company-summary__name-link::text',
        'company_info': 'ul.company-summary__list li.company-summary__item span.company-summary__text::text',
        'job_list': 'div.joblist-box__item.clearfix.joblist-box__item-unlogin',
        'job_id_pattern': r'"positionNumber":"(.*?)",',
        'next_page_btn': '/html/body/div[1]/div[4]/div[2]/div[2]/div/div[2]/div/div/a[7]',
        'search_input': '/html/body/div/div[1]/div/div[2]/div/div/div[2]/div/div/input',
        'search_btn': '//*[@id="root"]/div[1]/div/div[2]/div/div/div[2]/div/div/a',
    }

    def __init__(self, keyword: str, max_jobs: int = 20):
        self.keyword = keyword
        self.max_jobs = max_jobs
        self.browser: Optional[webdriver.Edge] = None
        self.wait: Optional[WebDriverWait] = None
        self.db: Optional[DatabaseManager] = None

    def _init_browser(self) -> None:
        """初始化浏览器"""
        options = Options()
        # options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(executable_path=CONFIG['EDGE_DRIVER_PATH'])
        self.browser = webdriver.Edge(service=service, options=options)
        self.browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        self.wait = WebDriverWait(self.browser, CONFIG['WAIT_TIMEOUT'])
        logger.info("浏览器初始化完成")

    def _init_database(self) -> None:
        """初始化数据库"""
        db_path = os.path.join(os.path.dirname(__file__), CONFIG['DB_NAME'])
        self.db = DatabaseManager(db_path)
        self.db.connect()

    def _perform_search(self) -> None:
        """在首页输入关键词并点击搜索"""
        self.browser.get(CONFIG['BASE_URL'])
        time.sleep(CONFIG['PAGE_LOAD_DELAY'])

        search_input = self.wait.until(
            EC.presence_of_element_located((By.XPATH, self.SELECTORS['search_input']))
        )
        search_input.clear()
        search_input.send_keys(self.keyword)
        logger.info(f"已输入搜索关键词: {self.keyword}")

        original_window = self.browser.current_window_handle
        original_windows = self.browser.window_handles

        search_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, self.SELECTORS['search_btn']))
        )
        search_btn.click()
        logger.info("已点击搜索按钮")

        self.wait.until(EC.new_window_is_opened(original_windows))
        new_windows = self.browser.window_handles
        new_window = [w for w in new_windows if w != original_window][0]
        self.browser.switch_to.window(new_window)
        logger.info(f"已切换到新窗口")

        self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, self.SELECTORS['job_list'])
        ))
        time.sleep(CONFIG['PAGE_LOAD_DELAY'])

        current_url = self.browser.current_url
        logger.info(f"原始URL: {current_url}")

        modified_url = re.sub(r'/jl\d+/', '/jl489/', current_url)
        if modified_url != current_url:
            self.browser.get(modified_url)
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.SELECTORS['job_list'])
            ))
            time.sleep(CONFIG['PAGE_LOAD_DELAY'])
            logger.info(f"已替换城市代码，新URL: {modified_url}")
        else:
            logger.info("URL中未找到/jl数字/模式，无需替换")

    def _get_job_ids_from_page(self) -> List[str]:
        """从当前页面获取岗位ID列表"""
        html = self.browser.page_source
        matches = re.findall(self.SELECTORS['job_id_pattern'], html)
        job_ids = [match.split('_')[0] for match in matches]
        return job_ids

    def _click_next_page(self) -> bool:
        """点击下一页"""
        try:
            next_btn = self.browser.find_element(By.XPATH, self.SELECTORS['next_page_btn'])
            if next_btn.is_enabled():
                next_btn.click()
                time.sleep(CONFIG['PAGE_LOAD_DELAY'])
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.SELECTORS['job_list'])
                ))
                time.sleep(CONFIG['PAGE_LOAD_DELAY'])
                return True
            return False
        except Exception as e:
            logger.warning(f"翻页失败: {e}")
            return False

    def _get_all_job_ids(self) -> List[str]:
        """获取所有岗位ID"""
        all_job_ids = []
        pages_needed = self.max_jobs // CONFIG['JOBS_PER_PAGE']
        
        for page in range(pages_needed):
            job_ids = self._get_job_ids_from_page()
            all_job_ids.extend(job_ids)
            logger.info(f"第 {page + 1} 页: 获取到 {len(job_ids)} 个岗位ID，累计 {len(all_job_ids)} 个")
            
            if page < pages_needed - 1:
                if not self._click_next_page():
                    logger.warning("无法翻到下一页，提前结束")
                    break
        
        return all_job_ids[:self.max_jobs]

    def _parse_job_detail(self, job_id: str) -> JobInfo:
        """解析岗位详情"""
        url = CONFIG['DETAIL_URL'].format(job_id=job_id)
        self.browser.get(url)
        time.sleep(CONFIG['PAGE_LOAD_DELAY'])

        selector = parsel.Selector(self.browser.page_source)

        job_name = selector.css(self.SELECTORS['job_name']).get() or '未知'
        job_salary = (selector.css(self.SELECTORS['job_salary']).get() or '未知').strip()

        raw_texts = selector.css(self.SELECTORS['detail_info']).getall()
        clean_list = [t.replace('|', '').strip() for t in raw_texts if t.replace('|', '').strip()]
        location = (selector.css('a.workCity-link::text').get() or '未知').strip()
        experience = clean_list[0] if len(clean_list) > 0 else '未知'
        education = clean_list[1] if len(clean_list) > 1 else '未知'

        desc_raw = selector.xpath(self.SELECTORS['job_description']).getall()
        desc_html = ''.join([t.strip() for t in desc_raw if t.strip()]) or ''
        desc_html = re.sub(r'<br\s*/?>', '\n', desc_html)
        desc_html = re.sub(r'<[^>]+>', '', desc_html)
        job_description = re.sub(r'\n\s*\n', '\n', desc_html).strip() or '未知'

        company_name = (selector.css(self.SELECTORS['company_name']).get() or '未知').strip()

        p_texts = selector.css(self.SELECTORS['company_info']).getall()
        company_type = p_texts[0].replace('性质：', '').strip() if len(p_texts) > 1 else '未知'
        company_size = p_texts[1].replace('人数：', '').strip() if len(p_texts) > 2 else '未知'
        industry = p_texts[2].replace('行业：', '').strip() if len(p_texts) > 0 else '未知'

        detail_url = f"https://www.zhaopin.com/jobdetail/{job_id}.htm?refcode=4019&srccode=401903&preactionid=c3225bd3-89bf-4d81-9f39-28152903b63a"

        return JobInfo(
            job_id=job_id, job_name=job_name, job_salary=job_salary,
            location=location, experience=experience, education=education,
            job_description=job_description, company_name=company_name,
            industry=industry, company_type=company_type, company_size=company_size,
            detail_url=detail_url
        )

    def run(self) -> None:
        """运行爬虫"""
        try:
            self._init_browser()
            self._init_database()

            self._perform_search()

            job_ids = self._get_all_job_ids()
            logger.info(f"共获取到 {len(job_ids)} 个岗位ID，开始爬取详情...")

            for idx, job_id in enumerate(job_ids, 1):
                job = self._parse_job_detail(job_id)
                self.db.save_job(job)
                logger.info(f"[{idx}/{len(job_ids)}] 已保存: {job.job_name} - {job.company_name}")

            logger.info(f"爬取完成，共保存 {len(job_ids)} 条岗位信息")

        except Exception as e:
            logger.error(f"爬取过程中发生错误: {e}")
            raise
        finally:
            if self.browser:
                self.browser.quit()
                logger.info("浏览器已关闭")
            if self.db:
                self.db.close()


def main():
    """主函数 - 独立运行爬虫"""
    keyword = input('请输入目标岗位名称: ').strip()
    if not keyword:
        logger.error("岗位名称不能为空")
        return

    while True:
        try:
            max_jobs = int(input('请输入爬取数量(需为20的倍数): ').strip())
            if max_jobs <= 0:
                logger.error("爬取数量必须大于0")
                continue
            if max_jobs % CONFIG['JOBS_PER_PAGE'] != 0:
                logger.error(f"爬取数量必须是{CONFIG['JOBS_PER_PAGE']}的倍数")
                continue
            break
        except ValueError:
            logger.error("请输入有效的数字")

    spider = ZhilianSpider(keyword, max_jobs)
    spider.run()


if __name__ == '__main__':
    main()
