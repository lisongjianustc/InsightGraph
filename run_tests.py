from playwright.sync_api import sync_playwright
import time
import os

def take_screenshots():
    os.makedirs("screenshots", exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def login(username, password):
            page.goto('http://localhost:5173/#/auth')
            page.wait_for_load_state('networkidle')
            page.fill('input[type="text"]', username)
            page.fill('input[type="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            time.sleep(2) # Give UI time to render feed
            
        def logout():
            # There might not be a logout button, so we just clear localStorage
            page.evaluate("localStorage.clear();")
            page.goto('http://localhost:5173/#/auth')
            page.wait_for_load_state('networkidle')
        
        # 1. Login as Alice
        print("Logging in as Alice...")
        login("alice_researcher", "Password@123")
        
        # Capture Alice's Capsules
        print("Capturing Alice's capsules...")
        page.goto('http://localhost:5173/#/capsule')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        page.screenshot(path="screenshots/alice_capsules.png")
        
        # Capture Alice's Graph
        print("Capturing Alice's graph...")
        page.goto('http://localhost:5173/#/graph')
        page.wait_for_load_state('networkidle')
        time.sleep(5) # Wait for echarts to render
        page.screenshot(path="screenshots/alice_graph.png")
        
        logout()
        
        # 2. Login as Bob
        print("Logging in as Bob...")
        login("bob_writer", "Password@123")
        
        # Capture Bob's Capsules
        print("Capturing Bob's capsules...")
        page.goto('http://localhost:5173/#/capsule')
        page.wait_for_load_state('networkidle')
        time.sleep(2)
        page.screenshot(path="screenshots/bob_capsules.png")
        
        # Capture Bob's Graph
        print("Capturing Bob's graph...")
        page.goto('http://localhost:5173/#/graph')
        page.wait_for_load_state('networkidle')
        time.sleep(5)
        page.screenshot(path="screenshots/bob_graph.png")
        
        # Test Global Chat isolation for Bob
        print("Testing Global Chat for Bob...")
        page.goto('http://localhost:5173/#/chat')
        page.wait_for_load_state('networkidle')
        time.sleep(1)
        
        # Find input and type
        # We need to find the chat input. Let's look for textarea or input
        page.fill('textarea', '我的知识库里有提到量子纠缠吗？或者实验室相关的内容？')
        # Click send button (usually an icon or "发送" button)
        # We can press Enter or click the button. Let's try Enter if textarea doesn't submit, or click a button
        page.keyboard.press('Enter')
        time.sleep(5) # Wait for response
        page.screenshot(path="screenshots/bob_chat.png")
        
        browser.close()
        print("Screenshots taken successfully!")

if __name__ == "__main__":
    take_screenshots()
