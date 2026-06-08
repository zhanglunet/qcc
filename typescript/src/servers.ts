export const Server = {
  COMPANY: "company",
  RISK: "risk",
  IPR: "ipr",
  OPERATION: "operation",
  EXECUTIVE: "executive",
  HISTORY: "history",
} as const;

export type Server = (typeof Server)[keyof typeof Server];

export const SERVERS: Record<Server, string> = {
  company: "企业工商基础 / 股东 / 注册信息",
  risk: "风险尽调 / 司法 / 失信 / 黑名单",
  ipr: "知识产权 / 专利 / 商标 / 资质",
  operation: "经营动态 / 财务 / 舆情",
  executive: "法代 / 高管 / 股东背调（双参数）",
  history: "企业历史轨迹（需企业认证）",
};

export const SERVER_KEYS = Object.keys(SERVERS) as Server[];
