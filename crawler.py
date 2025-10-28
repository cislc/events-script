import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging


class GiteeEventsCrawler:
    def __init__(self, config_path: str = "config.json"):
        """初始化爬虫"""
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.data_file = os.path.join(
            self.config["data_dir"],
            "events.jsonl"
        )
        self.state_file = os.path.join(
            self.config["data_dir"],
            "state.json"
        )

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _setup_logging(self):
        """设置日志"""
        os.makedirs(self.config["log_dir"], exist_ok=True)
        log_file = os.path.join(
            self.config["log_dir"],
            f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
        )

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_state(self) -> Optional[str]:
        """加载上次爬取的最新事件ID"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get("last_event_id")
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
        return None

    def _save_state(self, last_event_id: str):
        """保存最新事件ID"""
        state = {
            "last_event_id": last_event_id,
            "last_update": datetime.now().isoformat()
        }
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def fetch_events(self, prev_id: Optional[str] = None) -> List[Dict]:
        """获取组织事件"""
        url = f"{self.config['api_base_url']}/orgs/{self.config['organization']}/events"

        params = {
            "access_token": self.config["access_token"],
            "limit": self.config["limit"]
        }

        if prev_id:
            params["prev_id"] = prev_id

        try:
            self.logger.info(f"Fetching events from {url}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            events = response.json()
            self.logger.info(f"Fetched {len(events)} events")
            return events
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch events: {e}")
            return []

    def _save_events(self, events: List[Dict]):
        """保存事件到JSONL文件(每行一个JSON对象)"""
        os.makedirs(self.config["data_dir"], exist_ok=True)

        try:
            with open(self.data_file, 'a', encoding='utf-8') as f:
                for event in events:
                    # 添加爬取时间戳
                    event['_crawled_at'] = datetime.now().isoformat()
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
            self.logger.info(f"Saved {len(events)} events to {self.data_file}")
        except Exception as e:
            self.logger.error(f"Failed to save events: {e}")

    def get_new_events(self) -> List[Dict]:
        """增量获取新事件"""
        last_event_id = self._load_state()
        all_new_events = []

        if last_event_id:
            self.logger.info(f"Last event ID: {last_event_id}, fetching new events")
        else:
            self.logger.info("No previous state found, fetching all events")

        # 首次获取
        events = self.fetch_events()
        if not events:
            return all_new_events

        new_events = []
        stop_fetching = False

        for event in events:
            event_id = str(event.get('id', ''))
            if last_event_id and event_id == last_event_id:
                stop_fetching = True
                break
            new_events.append(event)

        all_new_events.extend(new_events)

        # 如果没有遇到上次的ID,继续翻页获取
        if not stop_fetching and events:
            last_id = str(events[-1].get('id', ''))
            page_count = 1
            max_pages = 10  # 防止无限循环

            while page_count < max_pages:
                events = self.fetch_events(prev_id=last_id)
                if not events:
                    break

                new_events = []
                for event in events:
                    event_id = str(event.get('id', ''))
                    if last_event_id and event_id == last_event_id:
                        stop_fetching = True
                        break
                    new_events.append(event)

                all_new_events.extend(new_events)

                if stop_fetching:
                    break

                last_id = str(events[-1].get('id', ''))
                page_count += 1

        return all_new_events

    def run(self):
        """运行爬虫"""
        self.logger.info("=" * 50)
        self.logger.info("Starting Gitee events crawler")
        self.logger.info("=" * 50)

        try:
            new_events = self.get_new_events()

            if new_events:
                self.logger.info(f"Found {len(new_events)} new events")
                # 保存事件(按时间正序保存,先反转列表)
                new_events.reverse()
                self._save_events(new_events)

                # 更新状态(最新的事件ID是原始列表的第一个)
                new_events.reverse()  # 恢复为倒序
                latest_event_id = str(new_events[0].get('id', ''))
                self._save_state(latest_event_id)
                self.logger.info(f"Updated state with latest event ID: {latest_event_id}")
            else:
                self.logger.info("No new events found")

            self.logger.info("Crawler finished successfully")

        except Exception as e:
            self.logger.error(f"Crawler error: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    crawler = GiteeEventsCrawler()
    crawler.run()
