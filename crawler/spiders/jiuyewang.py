# -*- coding: utf-8 -*-
"""就业在线岗位爬虫模块

该模块用于从 jobonline.cn 网站爬取岗位信息并存储到 SQLite 数据库。
"""

import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

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
from urllib3.util.ssl_ import create_urllib3_context

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


CONFIG = {
    'EDGE_DRIVER_PATH': r'E:\edgedriver_win64\msedgedriver.exe',
    'BASE_URL': 'https://jobonline.cn',
    'SEARCH_URL': 'https://jobonline.cn/findPositions?q={keyword}',
    'DETAIL_URL': 'https://jobonline.cn/positionDetail?id={job_id}&live=0&posiOriginate=JPOS0020',
    'DB_NAME': 'jobs.db',
    'WAIT_TIMEOUT': 20,
    'PAGE_LOAD_DELAY': 1,
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
    'JOBS_PER_PAGE': 20,
}


@dataclass
class JobInfo:
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

class DatabaseManager:
    """数据库管理类，负责岗位数据的存储。"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()
        logger.info(f"数据库连接成功: {self.db_path}")

    def _create_table(self) -> None:
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
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")


class JobOnlineSpider:
    """就业在线岗位爬虫类。"""

    SELECTORS = {
        'job_name': 'span.el-tooltip.name.item::text',
        'job_salary': 'span.theme-color::text',
        'detail_info': 'div.detailHead_middle span::text',
        'job_description': '//div[contains(@class, "text")]//text()',
        'company_name': 'div.desc h2::text',
        'company_info': 'div.desc p::text',
        'job_list': '.position-wrap .position_item',
        'job_id_pattern': r'<div data-v-d81f93e2="" id="(.*?)" class="LR_1"',
        'next_page_btn': '/html/body/mate/div/div[1]/div/div[3]/ul/div[3]/button[2]',
    }

    def __init__(self, keyword: str, max_jobs: int = 20):
        self.keyword = keyword
        self.max_jobs = max_jobs
        self.browser: Optional[webdriver.Edge] = None
        self.wait: Optional[WebDriverWait] = None
        self.db: Optional[DatabaseManager] = None

    def _init_browser(self) -> None:
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_argument("--headless=new")
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
        db_path = os.path.join(os.path.dirname(__file__), CONFIG['DB_NAME'])
        self.db = DatabaseManager(db_path)
        self.db.connect()

    def _get_job_ids_from_page(self) -> list[str]:
        html = self.browser.page_source
        matches = re.findall(self.SELECTORS['job_id_pattern'], html)
        job_ids = [match.split('_')[0] for match in matches]
        return job_ids

    def _click_next_page(self) -> bool:
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

    def _get_all_job_ids(self) -> list[str]:
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
        url = CONFIG['DETAIL_URL'].format(job_id=job_id)
        self.browser.get(url)
        time.sleep(CONFIG['PAGE_LOAD_DELAY'])

        selector = parsel.Selector(self.browser.page_source)

        job_name = selector.css(self.SELECTORS['job_name']).get() or '未知'
        job_salary = (selector.css(self.SELECTORS['job_salary']).get() or '未知').strip()

        raw_texts = selector.css(self.SELECTORS['detail_info']).getall()
        clean_list = [t.replace('|', '').strip() for t in raw_texts if t.replace('|', '').strip()]
        location = clean_list[0] if len(clean_list) > 0 else '未知'
        experience = clean_list[1] if len(clean_list) > 1 else '未知'
        education = clean_list[2] if len(clean_list) > 2 else '未知'

        desc_raw = selector.xpath(self.SELECTORS['job_description']).getall()
        job_description = ''.join([t.strip() for t in desc_raw if t.strip()]) or '未知'

        company_name = (selector.css(self.SELECTORS['company_name']).get() or '未知').strip()

        p_texts = selector.css(self.SELECTORS['company_info']).getall()
        industry = p_texts[0].replace('行业：', '').strip() if len(p_texts) > 0 else '未知'
        company_type = p_texts[1].replace('性质：', '').strip() if len(p_texts) > 1 else '未知'
        company_size = p_texts[2].replace('人数：', '').strip() if len(p_texts) > 2 else '未知'

        return JobInfo(
            job_id=job_id, job_name=job_name, job_salary=job_salary,
            location=location, experience=experience, education=education,
            job_description=job_description, company_name=company_name,
            industry=industry, company_type=company_type, company_size=company_size
        )

    def run(self) -> None:
        try:
            self._init_browser()
            self._init_database()

            search_url = CONFIG['SEARCH_URL'].format(keyword=self.keyword)
            self.browser.get(search_url)

            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.SELECTORS['job_list'])
            ))
            time.sleep(CONFIG['PAGE_LOAD_DELAY'])

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

    spider = JobOnlineSpider(keyword, max_jobs)
    spider.run()


if __name__ == '__main__':
    main()

