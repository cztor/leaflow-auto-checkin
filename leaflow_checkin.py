#!/usr/bin/env python3
"""
Leaflow 多账号自动签到脚本
变量名：LEAFLOW_ACCOUNTS
变量值：邮箱1:密码1,邮箱2:密码2,邮箱3:密码3
"""

import os
import time
import logging
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import requests
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LeaflowAutoCheckin:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        
        if not self.email or not self.password:
            raise ValueError("邮箱和密码不能为空")
        
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """设置Chrome驱动选项"""
        chrome_options = Options()
        
        # GitHub Actions环境配置
        if os.getenv('GITHUB_ACTIONS'):
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
        
        # 通用配置
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def close_popup(self):
        """关闭初始弹窗"""
        try:
            logger.info("尝试关闭初始弹窗...")
            time.sleep(3)  # 等待弹窗加载
            
            # 尝试关闭弹窗
            try:
                actions = ActionChains(self.driver)
                actions.move_by_offset(10, 10).click().perform()
                logger.info("已成功关闭弹窗")
                time.sleep(2)
                return True
            except:
                pass
            return False
            
        except Exception as e:
            logger.warning(f"关闭弹窗时出错: {e}")
            return False
    
    def wait_for_element_clickable(self, by, value, timeout=10):
        """等待元素可点击"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
    
    def wait_for_element_present(self, by, value, timeout=10):
        """等待元素出现"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def login(self):
        """执行登录流程"""
        logger.info(f"开始登录流程")
        
        # 访问登录页面
        self.driver.get("https://leaflow.net/login")
        time.sleep(5)
        
        # 关闭弹窗
        self.close_popup()
        
        # 输入邮箱
        try:
            logger.info("查找邮箱输入框...")
            
            # 等待页面稳定
            time.sleep(2)
            
            # 尝试多种选择器找到邮箱输入框
            email_selectors = [
                "input[type='text']",
                "input[type='email']", 
                "input[placeholder*='邮箱']",
                "input[placeholder*='邮件']",
                "input[placeholder*='email']",
                "input[name='email']",
                "input[name='username']"
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = self.wait_for_element_clickable(By.CSS_SELECTOR, selector, 5)
                    logger.info(f"找到邮箱输入框")
                    break
                except:
                    continue
            
            if not email_input:
                raise Exception("找不到邮箱输入框")
            
            # 清除并输入邮箱
            email_input.clear()
            email_input.send_keys(self.email)
            logger.info("邮箱输入完成")
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"输入邮箱时出错: {e}")
            # 尝试使用JavaScript直接设置值
            try:
                self.driver.execute_script(f"document.querySelector('input[type=\"text\"], input[type=\"email\"]').value = '{self.email}';")
                logger.info("通过JavaScript设置邮箱")
                time.sleep(2)
            except:
                raise Exception(f"无法输入邮箱: {e}")
        
        # 等待密码输入框出现并输入密码
        try:
            logger.info("查找密码输入框...")
            
            # 等待密码框出现
            password_input = self.wait_for_element_clickable(
                By.CSS_SELECTOR, "input[type='password']", 10
            )
            
            password_input.clear()
            password_input.send_keys(self.password)
            logger.info("密码输入完成")
            time.sleep(1)
            
        except TimeoutException:
            raise Exception("找不到密码输入框")
        
        # 点击登录按钮
        try:
            logger.info("查找登录按钮...")
            login_btn_selectors = [
                "//button[contains(text(), '登录')]",
                "//button[contains(text(), 'Login')]",
                "//button[@type='submit']",
                "//input[@type='submit']",
                "button[type='submit']"
            ]
            
            login_btn = None
            for selector in login_btn_selectors:
                try:
                    if selector.startswith("//"):
                        login_btn = self.wait_for_element_clickable(By.XPATH, selector, 5)
                    else:
                        login_btn = self.wait_for_element_clickable(By.CSS_SELECTOR, selector, 5)
                    logger.info(f"找到登录按钮")
                    break
                except:
                    continue
            
            if not login_btn:
                raise Exception("找不到登录按钮")
            
            login_btn.click()
            logger.info("已点击登录按钮")
            
        except Exception as e:
            raise Exception(f"点击登录按钮失败: {e}")
        
        # 等待登录完成
        try:
            WebDriverWait(self.driver, 20).until(
                lambda driver: "dashboard" in driver.current_url or "workspaces" in driver.current_url or "login" not in driver.current_url
            )
            
            # 检查当前URL确认登录成功
            current_url = self.driver.current_url
            if "dashboard" in current_url or "workspaces" in current_url or "login" not in current_url:
                logger.info(f"登录成功，当前URL: {current_url}")
                return True
            else:
                raise Exception("登录后未跳转到正确页面")
                
        except TimeoutException:
            # 检查是否登录失败
            try:
                error_selectors = [".error", ".alert-danger", "[class*='error']", "[class*='danger']"]
                for selector in error_selectors:
                    try:
                        error_msg = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if error_msg.is_displayed():
                            raise Exception(f"登录失败: {error_msg.text}")
                    except:
                        continue
                raise Exception("登录超时，无法确认登录状态")
            except Exception as e:
                raise e
    
    def get_balance(self):
        """获取当前账号的总余额"""
        try:
            logger.info("获取账号余额...")
            
            # 跳转到仪表板页面
            self.driver.get("https://leaflow.net/dashboard")
            time.sleep(3)
            
            # 等待页面加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 尝试多种选择器查找余额元素
            balance_selectors = [
                "//*[contains(text(), '¥') or contains(text(), '￥') or contains(text(), '元')]",
                "//*[contains(@class, 'balance')]",
                "//*[contains(@class, 'money')]",
                "//*[contains(@class, 'amount')]",
                "//button[contains(@class, 'dollar')]",
                "//span[contains(@class, 'font-medium')]"
            ]
            
            for selector in balance_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        # 查找包含数字和货币符号的文本
                        if any(char.isdigit() for char in text) and ('¥' in text or '￥' in text or '元' in text):
                            # 提取数字部分
                            import re
                            numbers = re.findall(r'\d+\.?\d*', text)
                            if numbers:
                                balance = numbers[0]
                                logger.info(f"找到余额: {balance}元")
                                return f"{balance}元"
                except:
                    continue
            
            logger.warning("未找到余额信息")
            return "未知"
            
        except Exception as e:
            logger.warning(f"获取余额时出错: {e}")
            return "未知"
    
    def wait_for_checkin_page_loaded(self, max_retries=3, wait_time=20):
        """等待签到页面完全加载，支持重试"""
        from selenium.common.exceptions import TimeoutException

        for attempt in range(max_retries):
            logger.info(f"等待签到页面加载，尝试 {attempt + 1}/{max_retries}")
            #logger.info(f"等待签到页面加载，尝试 {attempt + 1}/{max_retries}，等待 {wait_time} 秒...")
            #time.sleep(wait_time)
            
            try:
                # 检查页面是否包含签到相关元素
                # 使用组合等待条件：DOM就绪 + 核心元素可交互
                WebDriverWait(self.driver, wait_time).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            
                checkin_indicators = [
                    (By.CSS_SELECTOR, "button.checkin-btn"),  # 首选精确选择器
                    (By.XPATH, "//button[contains(text(), '立即签到')]"),
                    (By.XPATH, "//button[contains(text(), '已签到')]"),
                    (By.XPATH, "//button[contains(text(), '已完成')]"),
                    (By.XPATH, "//*[contains(text(), '每日签到')]"),
                    (By.XPATH, "//*[contains(text(), '签到')]")
                ]
                
                for locator_type, selector in checkin_indicators:
                    try:
                        # 使用短时等待提高效率
                        element = WebDriverWait(self.driver, 10).until(
                            EC.visibility_of_element_located((locator_type, selector))
                    )
                    
                        # 验证元素可交互状态
                        if element.is_enabled():
                            logger.info(f"检测到有效签到元素: {selector}")
                            return True
                    except TimeoutException:
                        logger.debug(f"元素定位失败: {selector}，尝试下个策略")
                        continue
                
                logger.warning(f"第 {attempt + 1} 次尝试未找到签到按钮，继续等待...")
                
            except TimeoutException:
                logger.error(f"页面加载超时，重试中... (尝试 {attempt+1})")
            except Exception as e:
                logger.critical(f"严重错误: {str(e)}")
                if "net::ERR" in str(e):
                    logger.info("检测到网络错误，立即重试")
                    continue
        
        return False
    
    def find_and_click_checkin_button(self):
        """查找并点击签到按钮 - 处理已签到状态"""
        logger.info("开始查找签到按钮...")
        start_time = time.time()
        
        try:
            # 收集页面基本信息
            logger.info(f"当前页面URL: {self.driver.current_url}")
            logger.info(f"当前页面标题: {self.driver.title}")
            
            # 先等待页面可能的重载
            logger.info("等待页面稳定...")
            time.sleep(5)
            
            # 使用和单账号成功时相同的选择器
            checkin_selectors = [
                "button.checkin-btn",
                "//button[contains(text(), '立即签到')]",
                "//button[contains(@class, 'checkin')]",
                "button[type='submit']",
                "button[name='checkin']"
            ]
            
            for selector in checkin_selectors:
                logger.info(f"尝试使用选择器: {selector}")
                try:
                    if selector.startswith("//"):
                        checkin_btn = WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        checkin_btn = WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    
                    # 详细检查按钮状态
                    logger.info(f"找到按钮，开始检查状态...")
                    logger.info(f"按钮可见性: {checkin_btn.is_displayed()}")
                    logger.info(f"按钮可用性: {checkin_btn.is_enabled()}")
                    logger.info(f"按钮文本: '{checkin_btn.text.strip()}'")
                    
                    if checkin_btn.is_displayed():
                        # 检查按钮文本，如果包含"已签到"或"已完成"则说明今天已经签到过了
                        btn_text = checkin_btn.text.strip()
                        
                        # 检查页面上是否有"今日已签到"文本
                        page_text = self.driver.page_source
                        
                        # 综合判断已签到状态：按钮禁用或按钮文本包含"已完成"或页面包含"今日已签到"
                        if (not checkin_btn.is_enabled() or 
                            "已完成" in btn_text or 
                            "今日已签到" in page_text or
                            "已签到" in btn_text):
                            logger.info(f"今日已签到，状态信息：")
                            logger.info(f"  - 按钮状态: {'禁用' if not checkin_btn.is_enabled() else '可用'}")
                            logger.info(f"  - 按钮文本: '{btn_text}'")
                            logger.info(f"  - 页面包含'今日已签到': {'是' if '今日已签到' in page_text else '否'}")
                            return "already_checked_in"
                        
                        # 尝试多种点击方式
                        clicked = False
                        
                        # 方式1: 直接点击
                        if checkin_btn.is_enabled():
                            try:
                                logger.info("方式1: 尝试直接点击按钮...")
                                checkin_btn.click()
                                clicked = True
                                logger.info("方式1: 直接点击成功")
                            except Exception as e:
                                logger.warning(f"方式1: 直接点击失败: {e}")
                                clicked = False
                        else:
                            logger.warning("按钮当前不可用，不应该到达这里，因为已在前面的检查中返回")
                        
                        # 方式2: JavaScript点击
                        if not clicked:
                            try:
                                logger.info("方式2: 尝试JavaScript点击...")
                                self.driver.execute_script("arguments[0].click();", checkin_btn)
                                clicked = True
                                logger.info("方式2: JavaScript点击成功")
                            except Exception as e:
                                logger.warning(f"方式2: JavaScript点击失败: {e}")
                                clicked = False
                        
                        # 方式3: ActionChains点击
                        if not clicked:
                            try:
                                logger.info("方式3: 尝试ActionChains点击...")
                                actions = ActionChains(self.driver)
                                actions.move_to_element(checkin_btn).click().perform()
                                clicked = True
                                logger.info("方式3: ActionChains点击成功")
                            except Exception as e:
                                logger.warning(f"方式3: ActionChains点击失败: {e}")
                                clicked = False
                        
                        if clicked:
                            logger.info(f"成功点击签到按钮，耗时: {time.time() - start_time:.2f}秒")
                            return True
                        else:
                            logger.error("所有点击方式均失败")
                            return False
                    else:
                        logger.warning("按钮不可见")
                        continue
                        
                except Exception as e:
                    logger.debug(f"选择器{selector}未找到按钮: {e}")
                    continue
            
            logger.error("遍历所有选择器后仍未找到可点击的签到按钮")
            return False
                    
        except Exception as e:
            logger.error(f"查找签到按钮时出错: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    
    def checkin(self):
        """执行签到流程"""
        logger.info("跳转到签到页面...")
        
        # 跳转到签到页面
        self.driver.get("https://checkin.leaflow.net")
        
        # 等待签到页面加载（最多重试3次，每次等待20秒）
        if not self.wait_for_checkin_page_loaded(max_retries=3, wait_time=20):
            raise Exception("签到页面加载失败，无法找到签到相关元素")
        
        # 查找并点击立即签到按钮
        checkin_result = self.find_and_click_checkin_button()
        
        if checkin_result == "already_checked_in":
            return "今日已签到"
        elif checkin_result is True:
            logger.info("已点击立即签到按钮")
            time.sleep(5)  # 等待签到结果
            
            # 获取签到结果
            result_message = self.get_checkin_result()
            return result_message
        else:
            raise Exception("找不到立即签到按钮或按钮不可点击")
    
    def get_checkin_result(self):
        """获取签到结果消息"""
        try:
            # 给页面一些时间显示结果
            time.sleep(3)
            
            # 尝试查找各种可能的成功消息元素
            success_selectors = [
                ".alert-success",
                ".success",
                ".message",
                "[class*='success']",
                "[class*='message']",
                ".modal-content",  # 弹窗内容
                ".ant-message",    # Ant Design 消息
                ".el-message",     # Element UI 消息
                ".toast",          # Toast消息
                ".notification"    # 通知
            ]
            
            for selector in success_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        text = element.text.strip()
                        if text:
                            return text
                except:
                    continue
            
            # 如果没有找到特定元素，检查页面文本
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            important_keywords = ["成功", "签到", "获得", "恭喜", "谢谢", "感谢", "完成", "已签到", "连续签到"]
            
            for keyword in important_keywords:
                if keyword in page_text:
                    # 提取包含关键词的行
                    lines = page_text.split('\n')
                    for line in lines:
                        if keyword in line and len(line.strip()) < 100:  # 避免提取过长的文本
                            return line.strip()
            
            # 检查签到按钮状态变化
            try:
                checkin_btn = self.driver.find_element(By.CSS_SELECTOR, "button.checkin-btn")
                if not checkin_btn.is_enabled() or "已签到" in checkin_btn.text or "disabled" in checkin_btn.get_attribute("class"):
                    return "今日已签到完成"
            except:
                pass
            
            return "签到完成，但未找到具体结果消息"
            
        except Exception as e:
            return f"获取签到结果时出错: {str(e)}"
    
    def run(self):
        """单个账号执行流程"""
        try:
            logger.info(f"开始处理账号")
            
            # 登录
            if self.login():
                # 签到
                result = self.checkin()
                
                # 获取余额
                balance = self.get_balance()
                
                logger.info(f"签到结果: {result}, 余额: {balance}")
                return True, result, balance
            else:
                raise Exception("登录失败")
                
        except Exception as e:
            error_msg = f"自动签到失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, "未知"
        
        finally:
            if self.driver:
                self.driver.quit()

class MultiAccountManager:
    """多账号管理器 - 简化配置版本"""
    
    def __init__(self):
        self.accounts = self.load_accounts()
    
    def load_accounts(self):
        """从环境变量加载多账号信息，支持冒号分隔多账号和单账号"""
        accounts = []
        
        logger.info("开始加载账号配置...")
        
        # 方法1: 冒号分隔多账号格式
        accounts_str = os.getenv('LEAFLOW_ACCOUNTS', '').strip()
        if accounts_str:
            try:
                logger.info("尝试解析冒号分隔多账号配置")
                account_pairs = [pair.strip() for pair in accounts_str.split(',')]
                
                logger.info(f"找到 {len(account_pairs)} 个账号")
                
                for i, pair in enumerate(account_pairs):
                    if ':' in pair:
                        email, password, token = pair.split(':', 1)
                        email = email.strip()
                        password = password.strip()
                        token = token.strip()
                        
                        if email and password:
                            accounts.append({
                                'email': email,
                                'password': password,
                                'token': token
                            })
                            logger.info(f"成功添加第 {i+1} 个账号")
                        else:
                            logger.warning(f"账号对格式错误")
                    else:
                        logger.warning(f"账号对缺少冒号分隔符")
                
                if accounts:
                    logger.info(f"从冒号分隔格式成功加载了 {len(accounts)} 个账号")
                    return accounts
                else:
                    logger.warning("冒号分隔配置中没有找到有效的账号信息")
            except Exception as e:
                logger.error(f"解析冒号分隔账号配置失败: {e}")
        
        # 方法2: 单账号格式
        single_email = os.getenv('LEAFLOW_EMAIL', '').strip()
        single_password = os.getenv('LEAFLOW_PASSWORD', '').strip()
        single_token = os.getenv('LEAFLOW_TOKEN', '').strip()
        if single_email and single_password:
            accounts.append({
                'email': single_email,
                'password': single_password,
                'token': single_token
            })
            logger.info("加载了单个账号配置")
            return accounts
        
        # 如果所有方法都失败
        logger.error("未找到有效的账号配置")
        logger.error("请检查以下环境变量设置:")
        logger.error("1. LEAFLOW_ACCOUNTS: 冒号分隔多账号 (email1:pass1,email2:pass2)")
        logger.error("2. LEAFLOW_EMAIL 和 LEAFLOW_PASSWORD: 单账号")
        
        raise ValueError("未找到有效的账号配置")
    
    def send_api_notification(self, message):
        """发送API通知"""
        try:
            url = "http://111.11.107.61:30005/send_private_msg"
            # 构建请求数据
            data = {
                "user_id": "8739050",
                "message": [{"type": "text", "data": {"text": message}}]
            }
            
            # 从环境变量读取token，默认值为heiheihaha
            token = os.getenv('LEAFLOW_TOKEN', '').strip()
            headers = {
                "Authorization": f"{token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"正在发送API通知到 {url}")
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            logger.info(f"API通知发送结果 - 状态码: {response.status_code}, 响应: {response.text}")
            logger.info(f"✅ API通知发送成功") if response.status_code == 200 else logger.error(f"❌ API通知发送失败")
                
        except Exception as e:
            logger.error(f"❌ 发送API通知时出错: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")
    
    def send_notification(self, results):
        """发送API通知"""
        logger.info("开始发送API通知")
        # 确保总是发送API通知，即使发生异常
        try:
            # 构建通知消息
            success_count = sum(1 for _, success, _, _ in results if success)
            total_count = len(results)
            current_date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            
            # 构建API通知消息
            api_message = f"🎁 Leaflow自动签到通知\n"
            api_message += f"📊 成功: {success_count}/{total_count}\n"
            api_message += f"📅 签到时间：{current_date}\n\n"
            
            for email, success, result, balance in results:
                # 隐藏邮箱部分字符以保护隐私
                masked_email = email[:3] + "***" + email[email.find("@"):]
                
                if success:
                    status = "✅"
                    api_message += f"账号：{masked_email}\n"
                    api_message += f"{status}  {result}！\n"
                    api_message += f"💰  当前总余额：{balance}。\n\n"
                else:
                    status = "❌"
                    api_message += f"账号：{masked_email}\n"
                    api_message += f"{status}  {result}\n\n"
            
            # 发送API通知
            logger.info("准备发送API通知")
            self.send_api_notification(api_message)
            logger.info("API通知发送完成")
            
        except Exception as e:
            logger.error(f"构建API通知消息时出错: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            # 即使发生异常，也要尝试发送基本的API通知
            try:
                success_count = sum(1 for _, success, _, _ in results if success)
                total_count = len(results)
                basic_message = f"签到任务完成，成功{success_count}个，失败{total_count - success_count}个"
                logger.info(f"尝试发送基本API通知: {basic_message}")
                self.send_api_notification(basic_message)
            except Exception as e2:
                logger.error(f"发送基本API通知时出错: {e2}")
                logger.error(f"错误详情: {traceback.format_exc()}")
    
    def run_all(self):
        """运行所有账号的签到流程"""
        logger.info(f"开始执行 {len(self.accounts)} 个账号的签到任务")
        
        results = []
        
        for i, account in enumerate(self.accounts, 1):
            logger.info(f"处理第 {i}/{len(self.accounts)} 个账号")
            
            try:
                auto_checkin = LeaflowAutoCheckin(account['email'], account['password'])
                success, result, balance = auto_checkin.run()
                results.append((account['email'], success, result, balance))
                
                # 在账号之间添加间隔，避免请求过于频繁
                if i < len(self.accounts):
                    wait_time = 5
                    logger.info(f"等待{wait_time}秒后处理下一个账号...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                error_msg = f"处理账号时发生异常: {str(e)}"
                logger.error(error_msg)
                results.append((account['email'], False, error_msg, "未知"))
        
        # 发送汇总通知
        self.send_notification(results)
        
        # 返回总体结果
        success_count = sum(1 for _, success, _, _ in results if success)
        return success_count == len(self.accounts), results

def main():
    """主函数"""
    try:
        manager = MultiAccountManager()
        overall_success, detailed_results = manager.run_all()
        
        if overall_success:
            logger.info("✅ 所有账号签到成功")
            exit(0)
        else:
            success_count = sum(1 for _, success, _, _ in detailed_results if success)
            logger.warning(f"⚠️ 部分账号签到失败: {success_count}/{len(detailed_results)} 成功")
            # 即使有失败，也不退出错误状态，因为可能部分成功
            exit(0)
            
    except Exception as e:
        logger.error(f"❌ 脚本执行出错: {e}")
        exit(1)

if __name__ == "__main__":
    main()
