"""系统设置 + 案例接口"""
from fastapi import APIRouter
from ..services import store
from .. import config

router = APIRouter(prefix="/api", tags=["settings"])

DEFAULT_SETTINGS = {
    "theme": "auto",
    "temperature": 0.65,
    "max_context_chars": config.MAX_CONTEXT_CHARS,
    "auto_summary": True,
    "site_title": "万能可视化工具",
}

@router.get("/settings")
async def get_settings():
    s = dict(DEFAULT_SETTINGS)
    for k in list(s.keys()):
        v = store.get_setting(k)
        if v is not None:
            s[k] = v
    return s

@router.post("/settings")
async def save_settings(payload: dict):
    for k, v in payload.items():
        if k in DEFAULT_SETTINGS:
            store.set_setting(k, v)
    return {"ok": True}

CASES = [
    {"id": "case-1", "name": "季度经营分析报告", "desc": "含营收结构与增长数据，适合演示图表洞察",
     "text": "2025年第三季度经营分析报告\n\n一、整体业绩：本季度实现营业收入 4,280 万元，同比增长 23.5%，环比增长 8.2%，完成年度目标的 78%。\n\n二、收入结构：智能硬件收入 2,150 万元（占 50.2%），软件订阅服务 1,320 万元（占 30.8%），技术服务 810 万元（占 18.9%）。软件订阅同比增长 45%，为增长最快的业务线。\n\n三、区域表现：华东区营收 1,540 万（36%）、华南区 1,110 万（26%）、华北区 890 万（21%）、其他区域 740 万（17%）。华东区同比增速达 31%。\n\n四、成本与利润：毛利率 42.3%，较上季度提升 1.8 个百分点；研发投入 640 万元，占营收 15%；净利润 520 万元，净利率 12.1%。\n\n五、用户数据：月活跃用户 38.6 万，付费转化率 9.2%，客户续约率 87%。NPS 净推荐值 46。\n\n六、四季度展望：重点推进企业版产品上线，预计软件订阅占比将提升至 35% 以上；华东华南保持高增长，加大华北区渠道投入。"},
    {"id": "case-2", "name": "产品发布演讲稿", "desc": "演讲型内容，适合时间线/亮点卡片版式",
     "text": "新一代智能手表 X5 发布会演讲稿\n\n开场：三年前我们重新思考了手表的意义。今天，X5 是我们交出的新答案。\n\n外观：X5 采用航天级钛合金表壳，重量仅 39 克，比上一代轻 18%。五种配色，表镜使用蓝宝石水晶。\n\n屏幕：1.5 英寸 LTPO 常显屏，峰值亮度 3000 尼特，阳光下清晰可见，功耗降低 25%。\n\n健康：全新三代传感器，血氧监测精度提升至医疗级 ±2%；新增血压趋势追踪与睡眠呼吸暂停筛查；心率异常提醒响应速度快至 30 秒。\n\n续航：智能模式续航 7 天，省电模式长达 21 天。快充 15 分钟可用一整天。\n\n生态：与手机、耳机、平板无缝协同，新增 200 款专属表盘，开放第三方应用市场。\n\n价格与发售：X5 售价 1,999 元起，即日起开启预订，10 月 8 日全渠道发售。首发送半年健康会员。"},
    {"id": "case-3", "name": "在线课程教学大纲", "desc": "教育类内容，适合清新版式与知识点结构化",
     "text": "Python 数据分析入门课程大纲（共 8 周）\n\n第1周 环境搭建与 Python 基础回顾：Anaconda/Jupyter 安装，变量与数据类型，列表字典操作，函数入门。练习：成绩单统计小程序。\n\n第2周 NumPy 数组计算：ndarray 创建与索引，广播机制，常用统计函数，性能对比练习。\n\n第3-4周 Pandas 数据处理：Series 与 DataFrame，数据读取（CSV/Excel/数据库），缺失值处理，groupby 聚合，merge 表连接。实战：电商订单数据清洗。\n\n第5周 数据可视化：Matplotlib 基础图形，Seaborn 统计图表，图表美化原则，如何讲好数据故事。\n\n第6周 统计分析基础：描述性统计，相关分析，假设检验入门，A/B 测试案例。\n\n第7周 综合项目：房价数据分析——从原始数据到分析报告全流程，含 5 张以上图表。\n\n第8周 结业展示：学员项目路演 + 代码复盘 + 进阶学习路线（机器学习方向/BI 方向）。\n\n考核方式：平时练习 30% + 综合项目 50% + 结业展示 20%。"},
]

@router.get("/cases")
async def cases():
    return CASES
