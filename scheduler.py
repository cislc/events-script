import schedule
import time
import logging
from crawler import GiteeEventsCrawler


def job():
    """定时任务"""
    crawler = GiteeEventsCrawler()
    crawler.run()


def main():
    """启动调度器"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # 每天凌晨1点执行
    schedule.every().day.at("01:00").do(job)

    logger.info("Scheduler started. Waiting for scheduled time (01:00 daily)...")
    logger.info("Press Ctrl+C to exit")

    # 可选: 启动时立即执行一次
    # job()

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
