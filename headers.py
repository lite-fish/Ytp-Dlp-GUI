def get_headers_by_selection(selection):
    """根据选择返回headers"""
    print(f"[headers模块] 接收到选择: {selection}")
    
    if selection == "PC":
        result = get_pc_headers()
    elif selection == "Mobile":
        result = get_mobile_headers()
    elif selection == "iOS":
        result = get_ios_headers()
    else:
        result = get_pc_headers()  # 默认
    
    print(f"[headers模块] 返回headers: {bool(result)}")
    return result

def get_pc_headers():
    """PC端headers - Chrome Windows"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Sec-CH-UA': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'Sec-CH-UA-Arch': '"x86"',
        'Sec-CH-UA-Bitness': '"64"',
        'Sec-CH-UA-Full-Version': '"141.0.7390.66"',
        'Sec-CH-UA-Full-Version-List': '"Google Chrome";v="141.0.7390.66", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.66"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Model': '""',
        'Sec-CH-UA-Platform': '"Windows"',
        'Sec-CH-UA-Platform-Version': '"19.0.0"',
        'Sec-CH-UA-WoW64': '?0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'X-Browser-Channel': 'stable',
        'X-Browser-Copyright': 'Copyright 2025 Google LLC. All rights reserved.',
        'X-Browser-Validation': 'AGaxImjg97xQkd0h3geRTArJi8Y=',
        'X-Browser-Year': '2025',
        'X-Client-Data': 'CIa2yQEIorbJAQipncoBCKj3ygEIkqHLAQiFoM0BCP2lzgEI6eTOAQj5hM8BCNSIzwEIy4vPAQiWjM8BCKSMzwEIjY7PAQilj88BGJiIzwEYxIvPAQ=='
    }

def get_mobile_headers():
    """移动端headers - Chrome Android"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Sec-CH-UA': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'Sec-CH-UA-Arch': '"arm"',
        'Sec-CH-UA-Bitness': '"64"',
        'Sec-CH-UA-Full-Version': '"141.0.7390.66"',
        'Sec-CH-UA-Full-Version-List': '"Google Chrome";v="141.0.7390.66", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.66"',
        'Sec-CH-UA-Mobile': '?1',
        'Sec-CH-UA-Model': '"SM-G973F"',
        'Sec-CH-UA-Platform': '"Android"',
        'Sec-CH-UA-Platform-Version': '"10.0.0"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
        'X-Browser-Channel': 'stable',
        'X-Browser-Copyright': 'Copyright 2025 Google LLC. All rights reserved.',
        'X-Browser-Validation': 'AGaxImjg97xQkd0h3geRTArJi8Y=',
        'X-Browser-Year': '2025',
        'X-Client-Data': 'CIa2yQEIorbJAQipncoBCKj3ygEIkqHLAQiFoM0BCP2lzgEI6eTOAQj5hM8BCNSIzwEIy4vPAQiWjM8BCKSMzwEIjY7PAQilj88BGJiIzwEYxIvPAQ==',
        'Viewport-Width': '414',
        'Width': '414'
    }

def get_ios_headers():
    """iOS端headers - Safari iOS"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
        'Sec-CH-UA': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'Sec-CH-UA-Mobile': '?1',
        'Sec-CH-UA-Platform': '"iOS"',
        'Sec-CH-UA-Platform-Version': '"17.1.0"',
        'Sec-CH-UA-Full-Version': '"114.0.5735.99"',
        'Sec-CH-UA-Arch': '"arm64"',
        'Sec-CH-UA-Model': '"iPhone14,2"',
        'Viewport-Width': '390',
        'Width': '390'
    }