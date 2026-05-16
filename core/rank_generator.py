import requests
import json

def generate_rank_image(group_id, day_count, members, api_url, access_token):
    """
    生成排行榜图片
    :param group_id: 群ID
    :param day_count: 统计天数
    :param members: 成员列表 [{"nickname": "xxx", "qq": "123", "count": 10}, ...]
    :param api_url: API 接口地址
    :param access_token: 访问令牌
    :return: 图片内容（bytes）或 None
    """
    
    # 1. 构造发送给 PHP 的 JSON 数据
    payload_data = {
        "group_id": group_id,
        "day_count": str(day_count), # 确保是字符串
        "list": members
    }
    
    # 2. 构造 POST 请求参数（包含 data 和 token）
    post_params = {
        "data": json.dumps(payload_data, ensure_ascii=False),
        "token": access_token
    }
    
    # 3. 设置 User-Agent 伪装
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) RankBot/2.0'
    }
    
    try:
        print(f"🚀 正在请求服务器生成 [{group_id}] 的 {day_count}日榜单...")
        
        # 发送请求
        response = requests.post(api_url, data=post_params, headers=headers, timeout=30)

        # 4. 处理响应
        if response.status_code == 200:
            # 检查返回的内容是否为 PNG 图片头
            if response.content.startswith(b'\x89PNG'):
                print("✅ 生成成功！")
                return response.content
            else:
                print("❌ 错误：服务器未返回有效的图片数据。")
                print("服务器提示:", response.text)
        elif response.status_code == 403:
            print("❌ 权限错误：Token 验证失败，请检查 ACCESS_TOKEN 是否正确。")
        else:
            print(f"❌ 服务器返回错误状态码: {response.status_code}")
            print("详情:", response.text)
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时：服务器响应时间过长，请检查网络或减少成员数量。")
    except Exception as e:
        print(f"❌ 运行异常: {e}")
    
    return None