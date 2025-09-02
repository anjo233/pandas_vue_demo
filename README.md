# 配置说明
1. 安装必要的库
$$ pip install "fastapi[all]" pandas "uvicorn[standard]" python-multipart aiofiles $$

$$ cd frontend $$
$$ npm install $$
npm install axios
 2. 安装Node.js[https://nodejs.org/zh-cn]
 3. 在backend文件夹的终端中，运行uvicorn:
$$ uvicorn main:app --reload  $$
 4. 在 frontend 文件夹的终端中，运行：
$$ npm run dev $$