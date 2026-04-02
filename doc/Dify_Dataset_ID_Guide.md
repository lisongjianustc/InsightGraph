# 如何在 Dify 中获取知识库 Dataset ID

在 Dify 的 Web 界面中，Dataset ID 是用来唯一标识一个知识库的 UUID 字符串。
当你需要通过 API（比如我们的 FastAPI 后端）对某个知识库进行“上传文档”、“检索”等操作时，必须在请求路径或环境变量中提供这个 ID。

### 获取方法

获取知识库 ID 有两种最简单的方法：

#### 方法一：通过浏览器 URL（最快捷）

1. 登录 Dify，进入顶部导航的 **知识库 (Knowledge)**。
2. 在知识库列表中，点击进入你想要获取 ID 的具体某个知识库（例如你截图中建立的 `InsightGraph DB`）。
3. 此时查看浏览器顶部的地址栏（URL）。
4. 它的格式通常是：
   `http://localhost:5001/datasets/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/documents`
5. 其中的 `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`（一长串字母数字组合）就是这个知识库的 **Dataset ID**。
6. 直接复制这串 UUID 即可。

#### 方法二：通过服务 API 页面

1. 在进入某个知识库的详情页面后，点击左侧导航栏的 **设置 (Settings)**，然后找到 **API** 相关的标签页。
   *(或者像你截图中那样，在知识库列表页点击右上角的 `服务 API` 按钮，然后选择对应的知识库)*
2. 在 API 参考文档页面，通常会提供一些代码示例（如 Curl, Python 等）。
3. 在这些示例代码的 URL 路径中，比如：
   `curl -X POST 'http://localhost:5001/v1/datasets/{dataset_id}/document/create_by_text' ...`
4. 代码中被替换在 `{dataset_id}` 位置的那串实际字符串，就是我们要找的 ID。

---

### 配置到项目环境变量

拿到不同分类知识库的 ID 后，打开你项目后端的 `/Users/lisongjian/Project/InsightGraph/backend/.env`（或项目根目录的 `.env`）文件，分别填入：

```env
# 这是你的全局 API 密钥，从 "服务 API" -> "API 密钥" 处生成获取
DIFY_API_KEY=dataset-xxxxxxxxxxxxxxxxxxxx

# 1. 默认/主知识库 ID (如果下面没有配置具体分类，系统会默认往这个库里存)
DIFY_DATASET_ID=11111111-1111-1111-1111-111111111111

# 2. 泛读分类知识库 ID
DIFY_DATASET_SKIM_ID=22222222-2222-2222-2222-222222222222

# 3. 原文分类知识库 ID
DIFY_DATASET_ORIGINAL_ID=33333333-3333-3333-3333-333333333333

# 4. 闪念胶囊知识库 ID
DIFY_DATASET_CAPSULE_ID=44444444-4444-4444-4444-444444444444
```

填好后，在终端执行 `docker compose restart backend` 重启后端容器即可生效。