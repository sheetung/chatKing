from utils.image_generator import RankingImageGenerator

if __name__ == '__main__':
    gen = RankingImageGenerator()
    data = [
        {"user_name": "测试用户一", "msg_count": 10},
        {"user_name": "第二用户", "msg_count": 7},
        {"user_name": "第三用户", "msg_count": 3},
    ]
    img_bytes = gen.generate_image_bytes(data, title="今日发言排行榜", date_str="2026-02-23")
    out_path = "/tmp/test_ranking.png"
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    print(f"Wrote image to {out_path}")
