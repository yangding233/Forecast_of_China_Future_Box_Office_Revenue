
### **1. 需求分析**

**主要需求：**
- **数据采集**：自动化抓取猫眼票房实时数据，需处理动态加密字体（防爬虫）。
- **多维度特征集成**：整合天气数据（北京、广州、上海、深圳四大城市）、节假日信息、星期权重等外部因素。
- **数据清洗与标准化**：对原始抓取数据进行去噪、缺失值填充、特征提取（如 Top3 电影的市场份额、上座率等）并统一日期格式。
- **票房趋势建模**：构建能够学习历史惯性（昨日票房、3/7日均值）和新片冲击（Has_New_Movie）的预测模型。
- **未来 7 天预测**：实现对未来一周大盘走势的自动化预测，并提供可视化图表输出。
- **业务逻辑修正**：针对 AI 预测可能出现的极端波动（如周五/周六大盘暴涨、工作日平稳期），引入业务逻辑锁（Floor Lock）和修正算法。

**1.1 数据采集子系统**
- **猫眼爬虫**：使用 Selenium 模拟浏览器行为，抓取实时大盘数据。
- **字体解密**：针对猫眼专有的 `.woff` 动态加密字体，通过坐标指纹识别技术实时还原数字信息。
- **天气采集**：获取主要消费城市的历史与未来天气评分，用于衡量天气对观影意愿的影响。

**1.2 预测与分析子系统**
- **模型训练**：基于历史清洗数据，训练梯度提升回归模型（HistGradientBoosting）。
- **动态模拟预测**：支持手动输入当前基准数据（日期、当前大盘、天气等），模拟未来 7 天的演变过程。
- **结果可视化**：生成直观的折线图，展示未来 7 天票房预测趋势。

---

### **2. 技术分析**

**核心语言：**
- **Python**：作为主要开发语言，负责爬虫、数据处理及建模。

**前端与采集：**
- **Selenium + ChromeDrive**：处理复杂的动态加载页面。
- **Requests**：用于下载字体文件和基础 API 请求。
- **FontTools (TTFont)**：解析 `.woff` 字体文件，提取字形坐标。

**数据处理与建模：**
- **Pandas**：核心数据洗炼工具，处理多表合并与滚动均值特征。
- **Numpy**：进行数值计算与矩阵操作。
- **Scikit-learn**：
  - `HistGradientBoostingRegressor`：用于处理包含缺失值和大规模特征的回归任务。
  - `MultiOutputRegressor`：实现多目标（未来 7 天）的同时预测。
- **Joblib**：用于模型的序列化存储与加载。

**可视化：**
- **Matplotlib**：绘制票房趋势预测图，支持中文字体显示。

---

### **3. 目录介绍**

项目分为核心预测逻辑模块和天气辅助模块。

#### **3.1 Data project-cyx 目录（核心逻辑）**
- **[scraper.py](file:///c:/Users/23353/Desktop/Forecast_of_China_Future_Box_Office_Revenue-main/Data_project/Data project-cyx/scraper.py)**：
  - `MaoyanSpider` 类：负责猫眼数据抓取。
  - `FontHandler` 类：核心黑科技，通过字形指纹识别解密加密字体。
- **[clean.py](file:///c:/Users/23353/Desktop/Forecast_of_China_Future_Box_Office_Revenue-main/Data_project/Data project-cyx/clean.py)**：
  - 数据预处理脚本，将天气、节假日、票房原始数据合并为 `final_data.csv`。
- **[train.py](file:///c:/Users/23353/Desktop/Forecast_of_China_Future_Box_Office_Revenue-main/Data_project/Data project-cyx/train.py)**：
  - 模型训练脚本，构建特征工程（滞后特征、趋势特征）并保存为 `best_model.pkl`。
- **[predictor.py](file:///c:/Users/23353/Desktop/Forecast_of_China_Future_Box_Office_Revenue-main/Data_project/Data project-cyx/predictor.py)**：
  - 预测交互脚本，加载模型并根据输入的当前数据，结合业务逻辑修正（如周五效应）输出未来 7 天预测值。
- **[base_font.woff](file:///c:/Users/23353/Desktop/Forecast_of_China_Future_Box_Office_Revenue-main/Data_project/Data project-cyx/base_font.woff)**：
  - 基础字体库文件，用于指纹对比。

#### **3.2 weather-yjh 目录（天气模块）**
- **[天气爬虫.py](file:///c:/Users/23353/Desktop/Forecast_of_China_Future_Box_Office_Revenue-main/Data_project/weather-yjh/天气爬虫.py)**：
  - 负责抓取北京、上海等地的历史天气数据。
- **[天气.js](file:///c:/Users/23353/Desktop/Forecast_of_China_Future_Box_Office_Revenue-main/Data_project/weather-yjh/天气.js)**：
  - Node.js 环境下的天气处理辅助逻辑。

---

### **4. 项目启用方式**

**预先准备：**
- Python 3.8+ 环境。
- 安装 Chrome 浏览器及对应版本的 [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/)。
- 安装依赖库：
  ```bash
  pip install pandas numpy scikit-learn selenium requests fontTools matplotlib joblib
  ```

**运行流程：**

1. **执行数据抓取**：
   运行 `scraper.py` 获取最新的票房原始数据 `maoyan_data.csv`。
2. **执行天气获取**：
   运行 `天气爬虫.py` 获取各地天气 CSV 文件。
3. **数据清洗与合并**：
   运行 `clean.py`，生成标准化的训练数据集 `final_data.csv`。
4. **模型训练**：
   运行 `train.py`，训练并生成 `best_model.pkl` 模型文件。
5. **票房预测**：
   运行 `predictor.py`，根据命令行提示输入当前大盘参数，即可在弹出的窗口中查看未来 7 天的预测走势。

---

### **5. 核心逻辑亮点**

- **防爬攻坚**：通过计算字形坐标的网格指纹（Fingerprint），解决了猫眼每页随机生成字体编码的难题。
- **业务纠偏**：在 AI 纯数值预测的基础上，加入了“周五强力反弹”、“周六爆发”、“工作日稳定性”等人工干预逻辑，使预测结果更符合电影市场的真实商业规律。
