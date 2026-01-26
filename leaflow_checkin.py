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
from selenium.common.exceptions import TimeoutException
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
                
                # 获取并保存登录后的COOKIE
                logger.info("获取登录后的COOKIE...")
                self.login_cookies = self.driver.get_cookies()
                logger.info(f"获取到 {len(self.login_cookies)} 个COOKIE")
                for cookie in self.login_cookies:
                    logger.debug(f"COOKIE: {cookie['name']} -> {cookie['domain']}")
                    
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

        for attempt in range(max_retries):
            logger.info(f"等待签到页面加载，尝试 {attempt + 1}/{max_retries}")
            
            # 收集页面基本信息，便于调试
            logger.info(f"  当前页面URL: {self.driver.current_url}")
            logger.info(f"  当前页面标题: {self.driver.title}")
            
            try:
                # 检查页面是否包含签到相关元素
                # 使用组合等待条件：DOM就绪 + 核心元素可见
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
                    
                        # 只要找到可见的签到相关元素，不管是否可用，都认为页面已加载成功
                        # 已签到状态下的按钮可能是禁用的，所以不能用is_enabled()判断
                        logger.info(f"检测到签到元素: {selector}")
                        logger.info(f"  元素可见性: {element.is_displayed()}")
                        logger.info(f"  元素可用性: {'启用' if element.is_enabled() else '禁用'}")
                        logger.info(f"  元素文本: '{element.text.strip()}'")
                        return True
                    except TimeoutException:
                        logger.debug(f"元素定位失败: {selector}，尝试下个策略")
                        continue
                
                logger.warning(f"第 {attempt + 1} 次尝试未找到签到相关元素")
                
                # 尝试获取页面源代码的前2000个字符，便于调试
                try:
                    page_source = self.driver.page_source[:2000]
                    logger.debug(f"页面源码片段: {page_source}...")
                except Exception as e:
                    logger.error(f"获取页面源码失败: {e}")
                
            except TimeoutException:
                logger.error(f"页面加载超时，重试中... (尝试 {attempt+1})")
            except Exception as e:
                logger.critical(f"严重错误: {str(e)}")
                logger.error(f"错误详情: {traceback.format_exc()}")
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
                        
                        # 方式1: JavaScript点击（优先使用，避免页面阻塞）
                        try:
                            logger.info("方式1: 尝试JavaScript点击...")
                            self.driver.execute_script("arguments[0].click();", checkin_btn)
                            clicked = True
                            logger.info("方式1: JavaScript点击成功")
                        except Exception as e:
                            logger.warning(f"方式1: JavaScript点击失败: {e}")
                            clicked = False
                        
                        # 方式2: ActionChains点击
                        if not clicked:
                            try:
                                logger.info("方式2: 尝试ActionChains点击...")
                                # 设置隐式等待时间，避免点击超时
                                self.driver.implicitly_wait(5)
                                actions = ActionChains(self.driver)
                                actions.move_to_element(checkin_btn).click().perform()
                                clicked = True
                                logger.info("方式2: ActionChains点击成功")
                            except Exception as e:
                                logger.warning(f"方式2: ActionChains点击失败: {e}")
                                clicked = False
                            finally:
                                # 恢复隐式等待时间
                                self.driver.implicitly_wait(0)
                        
                        # 方式3: 直接点击（最后尝试，可能会阻塞）
                        if not clicked:
                            try:
                                logger.info("方式3: 尝试直接点击按钮...")
                                # 使用WebDriverWait设置点击超时
                                WebDriverWait(self.driver, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.checkin-btn"))
                                ).click()
                                clicked = True
                                logger.info("方式3: 直接点击成功")
                            except Exception as e:
                                logger.warning(f"方式3: 直接点击失败: {e}")
                                clicked = False
                        
                        if clicked:
                            logger.info(f"成功点击签到按钮，耗时: {time.time() - start_time:.2f}秒")
                            # 点击后立即检查页面变化，确认签到是否成功
                            time.sleep(2)
                            # 检查按钮状态或页面文本变化
                            try:
                                updated_btn = self.driver.find_element(By.CSS_SELECTOR, "button.checkin-btn")
                                updated_text = updated_btn.text.strip()
                                page_text = self.driver.page_source
                                if (not updated_btn.is_enabled() or 
                                    "已完成" in updated_text or 
                                    "今日已签到" in page_text or
                                    "已签到" in updated_text):
                                    logger.info("签到成功，按钮状态已更新")
                            except:
                                pass
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
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    
    def checkin(self):
        """执行签到流程"""
        logger.info("执行签到流程...")
        
        # 跳转到签到页面
        logger.info("跳转到签到页面...")
        
        # 网络请求重试设置
        max_retries = 3
        retry_delay = 5  # 秒
        
        # 尝试访问签到页面，处理网络超时
        for attempt in range(1, max_retries + 1):
            try:
                # 设置页面加载超时
                self.driver.set_page_load_timeout(30)
                
                logger.info(f"尝试第 {attempt}/{max_retries} 次访问签到页面...")
                # 先访问checkin域名主页，设置好域名上下文
                self.driver.get("https://checkin.leaflow.net")
                logger.info(f"成功访问签到页面，URL: {self.driver.current_url}")
                
                # 添加登录时保存的COOKIE到当前域名
                logger.info("添加登录COOKIE到checkin域名...")
                if hasattr(self, 'login_cookies') and self.login_cookies:
                    # 先访问checkin域名的一个简单页面，确保域名上下文正确
                    self.driver.get("https://checkin.leaflow.net/")
                    
                    # 先清除当前页面的COOKIE
                    self.driver.delete_all_cookies()
                    
                    # 添加登录时保存的所有COOKIE
                    for cookie in self.login_cookies:
                        try:
                            # 适配不同域名的COOKIE
                            cookie_copy = cookie.copy()
                            # 确保COOKIE能被所有子域名使用
                            if 'domain' not in cookie_copy or not cookie_copy['domain']:
                                cookie_copy['domain'] = '.leaflow.net'
                            # 移除可能导致问题的属性
                            if 'expiry' in cookie_copy and isinstance(cookie_copy['expiry'], float):
                                cookie_copy['expiry'] = int(cookie_copy['expiry'])
                            # 添加COOKIE
                            self.driver.add_cookie(cookie_copy)
                            logger.debug(f"添加COOKIE成功: {cookie['name']} -> {cookie_copy.get('domain', '无域名')}")
                        except Exception as e:
                            logger.debug(f"添加COOKIE失败: {cookie['name']} -> {e}")
                    
                    # 不使用refresh()，而是直接访问签到首页，避免页面阻塞
                    logger.info("COOKIE添加完成，直接访问签到首页...")
                    
                    # 尝试访问签到首页，捕获超时异常
                    try:
                        # 使用较短的超时时间，避免长时间等待
                        self.driver.set_page_load_timeout(15)  # 设置合理的超时时间
                        self.driver.get("https://checkin.leaflow.net/")
                        logger.info(f"成功访问签到首页，URL: {self.driver.current_url}")
                    except Exception as e:
                        logger.error(f"访问签到首页时出错: {e}")
                        # 无论是否超时，都获取当前页面信息
                        try:
                            logger.info(f"当前页面URL: {self.driver.current_url}")
                            logger.info(f"当前页面标题: {self.driver.title}")
                            # 获取页面源码（最多前2000字符）
                            page_source = self.driver.page_source[:2000]
                            logger.info(f"页面源码片段: {page_source}")
                        except Exception as info_e:
                            logger.error(f"获取页面信息失败: {info_e}")
                    finally:
                        # 恢复默认超时时间
                        self.driver.set_page_load_timeout(60)
                
                # 获取当前页面信息，便于调试
                logger.info(f"当前签到页面URL: {self.driver.current_url}")
                logger.info(f"当前页面标题: {self.driver.title}")
                
                # 简化重定向处理，直接检查当前URL
                logger.info("检查当前页面状态...")
                
                # 检查是否需要进行OAuth授权
                if "oauth/authorize" in self.driver.current_url:
                    logger.info("检测到OAuth授权页面，尝试自动授权...")
                    # 查找并点击授权按钮
                    try:
                        # 尝试多种选择器找到授权按钮
                        authorize_selectors = [
                            "button[type='submit']",
                            "input[type='submit']",
                            "//button[contains(text(), '授权')]",
                            "//button[contains(text(), 'Authorize')]"
                        ]
                        
                        authorize_btn = None
                        for selector in authorize_selectors:
                            try:
                                if selector.startswith("//"):
                                    authorize_btn = WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                else:
                                    authorize_btn = WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                logger.info(f"找到授权按钮")
                                break
                            except:
                                continue
                        
                        if authorize_btn:
                            authorize_btn.click()
                            logger.info("已点击授权按钮")
                            time.sleep(5)
                            logger.info(f"授权后URL: {self.driver.current_url}")
                        else:
                            logger.warning("未找到授权按钮，尝试等待自动跳转...")
                            time.sleep(10)
                            logger.info(f"等待后URL: {self.driver.current_url}")
                    except Exception as e:
                        logger.warning(f"自动授权失败，可能需要手动授权: {e}")
                
                break  # 成功访问并处理完重定向，跳出重试循环
                
            except Exception as e:
                if "ERR_CONNECTION_TIMED_OUT" in str(e) or "timeout" in str(e).lower():
                    logger.error(f"第 {attempt} 次访问签到页面超时: {e}")
                    if attempt < max_retries:
                        logger.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        logger.error(f"经过 {max_retries} 次重试后仍无法访问签到页面")
                        raise
                else:
                    logger.error(f"访问签到页面时发生其他错误: {e}")
                    raise
            finally:
                # 恢复默认页面加载超时
                self.driver.set_page_load_timeout(60)
        
        # 等待签到页面加载（最多重试5次，每次等待20秒）
        retry_count = 0
        max_retries = 5
        success = False
        
        while retry_count < max_retries and not success:
            retry_count += 1
            logger.info(f"等待签到页面加载，尝试 {retry_count}/{max_retries}")
            
            # 检查当前URL和标题，记录详细信息
            current_url = self.driver.current_url
            current_title = self.driver.title
            logger.info(f"  当前URL: {current_url}")
            logger.info(f"  当前标题: {current_title}")
            
            # 检查是否是502错误
            if "502" in current_title or "Bad Gateway" in current_title:
                logger.error(f"第 {retry_count} 次尝试遇到502 Bad Gateway错误")
                
                # 尝试重新访问主站获取有效COOKIE（仅在需要时）
                logger.info("尝试重新访问主站获取有效COOKIE...")
                self.driver.get("https://leaflow.net/dashboard")
                time.sleep(3)
                
                # 重新跳转到签到页面
                self.driver.get("https://checkin.leaflow.net")
                time.sleep(5)
                continue
            
            # 检查是否是重定向到登录页面
            if "login" in current_url and "checkin" not in current_url:
                logger.error(f"第 {retry_count} 次尝试遇到登录页面，COOKIE可能失效")
                
                # 重新执行登录流程
                logger.info("尝试重新登录...")
                if self.login():
                    # 重新跳转到签到页面
                    self.driver.get("https://checkin.leaflow.net")
                    time.sleep(5)
                else:
                    raise Exception("重新登录失败")
                continue
            
            # 检查是否是OAuth回调页面
            if "auth_callback.php" in current_url:
                logger.info(f"第 {retry_count} 次尝试遇到OAuth回调页面，等待自动跳转...")
                time.sleep(5)
                logger.info(f"  自动跳转后URL: {self.driver.current_url}")
                logger.info(f"  自动跳转后标题: {self.driver.title}")
            
            # 尝试等待页面加载
            if self.wait_for_checkin_page_loaded(max_retries=1, wait_time=15):
                success = True
                logger.info(f"第 {retry_count} 次尝试成功加载签到页面")
            else:
                logger.warning(f"第 {retry_count} 次尝试未成功加载签到页面")
                
                # 尝试刷新页面
                logger.info("尝试刷新页面...")
                self.driver.refresh()
                time.sleep(5)
        
        if not success:
            raise Exception(f"签到页面加载失败，经过 {max_retries} 次重试后仍无法访问")
        
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
            
            # 从环境变量读取token
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
        
        # 发送第一次汇总通知
        self.send_notification(results)
        
        # 暂时关闭30分钟后重试功能
        # 检查是否有失败的账号需要重试
        # failed_accounts = [account for account, (email, success, _, _) in zip(self.accounts, results) if not success]
        # if failed_accounts:
        #     logger.info(f"发现 {len(failed_accounts)} 个账号签到失败，将在30分钟后重试...")
        #     
        #     # 等待30分钟
        #     retry_wait_time = 30 * 60
        #     logger.info(f"等待{retry_wait_time}秒后重试失败的账号...")
        #     time.sleep(retry_wait_time)
        #     
        #     # 重试失败的账号
        #     retry_results = []
        #     for i, account in enumerate(failed_accounts, 1):
        #         logger.info(f"重试第 {i}/{len(failed_accounts)} 个失败账号")
        #         
        #         try:
        #             auto_checkin = LeaflowAutoCheckin(account['email'], account['password'])
        #             success, result, balance = auto_checkin.run()
        #             retry_results.append((account['email'], success, result, balance))
        #             
        #             # 在账号之间添加间隔
        #             if i < len(failed_accounts):
        #                 wait_time = 5
        #                 logger.info(f"等待{wait_time}秒后处理下一个重试账号...")
        #                 time.sleep(wait_time)
        #                 
        #         except Exception as e:
        #             error_msg = f"重试账号时发生异常: {str(e)}"
        #             logger.error(error_msg)
        #             retry_results.append((account['email'], False, error_msg, "未知"))
        #     
        #     # 发送重试结果通知
        #     if retry_results:
        #         # 构建重试通知消息
        #         retry_success_count = sum(1 for _, success, _, _ in retry_results if success)
        #         retry_total_count = len(retry_results)
        #         current_date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        #         
        #         retry_message = f"🔄 Leaflow自动签到重试通知\n"
        #         retry_message += f"📊 重试成功: {retry_success_count}/{retry_total_count}\n"
        #         retry_message += f"📅 重试时间：{current_date}\n\n"
        #         
        #         for email, success, result, balance in retry_results:
        #             masked_email = email[:3] + "***" + email[email.find("@"):]
        #             
        #             if success:
        #                 status = "✅"
        #                 retry_message += f"账号：{masked_email}\n"
        #                 retry_message += f"{status}  重试成功！{result}\n"
        #                 retry_message += f"💰  当前总余额：{balance}。\n\n"
        #             else:
        #                 status = "❌"
        #                 retry_message += f"账号：{masked_email}\n"
        #                 retry_message += f"{status}  重试失败：{result}\n\n"
        #         
        #         # 发送重试通知
        #         logger.info("发送重试结果通知...")
        #         self.send_api_notification(retry_message)
        #         
        #         # 更新原始结果
        #         for email, success, result, balance in retry_results:
        #             for i, (orig_email, orig_success, orig_result, orig_balance) in enumerate(results):
        #                 if orig_email == email:
        #                     results[i] = (email, success, result, balance)
        #                     break
        
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
