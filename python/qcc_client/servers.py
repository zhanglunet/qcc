from enum import Enum


class Server(str, Enum):
    COMPANY = "company"
    RISK = "risk"
    IPR = "ipr"
    OPERATION = "operation"
    EXECUTIVE = "executive"
    HISTORY = "history"


SERVERS: dict[Server, str] = {
    Server.COMPANY: "企业工商基础 / 股东 / 注册信息",
    Server.RISK: "风险尽调 / 司法 / 失信 / 黑名单",
    Server.IPR: "知识产权 / 专利 / 商标 / 资质",
    Server.OPERATION: "经营动态 / 财务 / 舆情",
    Server.EXECUTIVE: "法代 / 高管 / 股东背调（双参数）",
    Server.HISTORY: "企业历史轨迹（需企业认证）",
}
