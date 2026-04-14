# AI Writer (AI 魔法棒) 自动化测试报告

此报告由自动化脚本生成，验证 AI 魔法重写接口在不同模式下的表现。

## 测试 1：模板模式 - action_items
### Request Payload
```json
{
  "draft_content": "今天开了个会，讨论新项目开发。张三负责写前端页面，李四负责后端接口，下周三之前搞定。我还要给老板发个邮件汇报进度。",
  "reference_capsule_ids": [],
  "reference_feed_ids": [],
  "reference_original_ids": [],
  "mode": "template",
  "template_id": "action_items",
  "custom_prompt": ""
}
```
**HTTP Status**: 200

### Streamed Response (first 1000 chars)
```markdown

[Stream Error: HTTPConnectionPool(host='127.0.0.1', port=8000): Read timed out.]
```

## 测试 2：模板模式 + 附加要求 (expand)
### Request Payload
```json
{
  "draft_content": "AI 的发展非常迅速，对各行各业都产生了影响。",
  "reference_capsule_ids": [],
  "reference_feed_ids": [],
  "reference_original_ids": [],
  "mode": "template",
  "template_id": "expand",
  "custom_prompt": "请用生动的比喻，并举 2 个具体的行业例子。"
}
```
**HTTP Status**: 200

### Streamed Response (first 1000 chars)
```markdown

[Stream Error: HTTPConnectionPool(host='127.0.0.1', port=8000): Read timed out.]
```

## 测试 3：完全自定义模式
### Request Payload
```json
{
  "draft_content": "昨天学了 Rust 的所有权机制，感觉很难懂。主要是所有权借用和生命周期这块，老是报错。",
  "reference_capsule_ids": [],
  "reference_feed_ids": [],
  "reference_original_ids": [],
  "mode": "custom",
  "custom_prompt": "写一首五言绝句总结这段话的心情。"
}
```
**HTTP Status**: 200

### Streamed Response (first 1000 chars)
```markdown
# 今日笔记：Rust 所有权机制初探

## 核心概念
- **所有权**：Rust 的核心安全机制，每个值有且只有一个所有者
- **借用**：通过引用访问数据而不获取所有权，分为不可变借用（&T）和可变借用（&mut T）
- **生命周期**：确保引用始终有效，编译器通过生命周期标注验证引用安全性

## 学习难点
1. 所有权转移时的编译错误频繁出现
2. 借用规则理解不透彻（同一时间只能有一个可变引用或多个不可变引用）
3. 生命周期标注语法复杂，实际应用场景模糊

## 实践体会
尝试编写简单结构体时，频繁遇到“value borrowed here after move”和“cannot borrow as mutable”等错误。需要更系统地理解借用检查器的运作逻辑。

---

**学习心情总结：**

困惑如迷雾，  
代码报错频。  
借期难掌握，  
苦思至夜深。
```

## 测试 4：旧版格式兼容 (format_type)
### Request Payload
```json
{
  "draft_content": "这是一个简单的测试句子。",
  "reference_capsule_ids": [],
  "reference_feed_ids": [],
  "reference_original_ids": [],
  "format_type": "card"
}
```
**HTTP Status**: 200

### Streamed Response (first 1000 chars)
```markdown
*   🚀 **启动预热**：系统在用户输入前并行初始化权限、工具和 MCP 连接，以缩短后续查询的响应时间。
*   📦 **上下文组装**：请求发送前，会预先整合系统规则、项目信息和环境状态三类上下文，而非简单转发用户输入。
*   🔁 **核心循环**：查询引擎通过“整理消息 -> 调用模型 -> 识别工具 -> 执行工具 -> 回流结果”的循环，持续处理直至任务完成。
*   🛠️ **工具封装**：模型所见的工具能力是经过封装和管理的特定接口，而非直接暴露所有系统能力。
```

