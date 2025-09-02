<script setup>
import { ref, onMounted, nextTick, watch,computed } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';

// --- 状态定义 ---
const salesData = ref([]);
const kpiData = ref(null);
const growthData = ref([]);
// 控制UI状态
const loading = ref(true);
const error = ref(null);

const lineChartContainer = ref(null); 
const pieChartContainer = ref(null);  // 2. 为饼图新增 ref
const growthChartContainer = ref(null);
// 用于筛选器
const allMonths = ref([]);
const startMonth = ref(null);
const endMonth = ref(null);
//存放Echarts实例
let lineChart = null; // 折线图实例
let pieChart = null;  // 饼图实例
let growthChart = null; // 增长率图实例
// --- 计算属性 ---
// 计算当前筛选范围内的总销售额
const totalSales = computed(() => {
  // 使用 a.reduce() 方法来累加数组中的销售额
  // a.reduce((sum, item) => sum + item.sales, 0)
  // sum: 累加器，初始值为 0
  // item: 数组中的当前项
  return salesData.value.reduce((sum, item) => sum + item.sales, 0);
});

// 计算饼图数据
const pieChartData = computed(() => {
  if (!kpiData.value || kpiData.value.total_sales === 0) {
    return []; // 如果KPI数据还没加载，返回空数组
  }
  
  const selectedValue = totalSales.value;
  const otherValue = kpiData.value.total_sales - selectedValue;

  // 返回 ECharts 饼图需要的数据格式
  return [
    { value: selectedValue, name: '选中范围销售额' },
    { value: otherValue, name: '其他月份销售额' },
  ];
});


// --- 主要的数据获取函数 ---
async function fetchData() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/sales', {
      params: { start_month: startMonth.value, end_month: endMonth.value }
    });
    salesData.value = response.data;
  } catch (e) { console.error("无法加载销售数据:", e); 
                error.value = '无法加载销售数据'; }
}


// 从后端获取KPI数据
async function fetchKpiData() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/kpi');
    kpiData.value = response.data;
  } catch (e) {
    console.error("无法加载KPI数据:", e);
    // 也可以设置一个专门的错误状态
  }
}

// 从后端获取增长率数据
async function fetchGrowthData() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/month_pct', {
      params: { start_month: startMonth.value, end_month: endMonth.value }
    });
    growthData.value = response.data;
  } catch (e) { console.error("无法加载增长率数据:", e); 
                error.value = '无法加载增长率数据'; }
}

// --- 图表更新/初始化的辅助函数 ---
function updateLineChart() {
  if (!lineChart && lineChartContainer.value) {
    lineChart = echarts.init(lineChartContainer.value);
  }

  if (lineChart) {
    const xAxisData = salesData.value.map(item => item.month);
    const seriesData = salesData.value.map(item => item.sales);
    const option = {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: xAxisData },
      yAxis: { type: 'value' },
      series: [{
        name: '销售额',
        data: seriesData,
        type: 'line',
        smooth: true
      }]
    };
    lineChart.setOption(option);
  }
}

// 更新饼图
function updatePieChart() {
  if (!pieChart && pieChartContainer.value) {
    pieChart = echarts.init(pieChartContainer.value);
  }
  if (pieChart) {
    const option = {
      title: {
        text: '销售额占比',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)' // 提示框格式
      },
      legend: {
        orient: 'vertical',
        left: 'left',
      },
      series: [{
        name: '销售额',
        type: 'pie',
        radius: '50%',
        data: pieChartData.value, // 使用计算属性提供数据
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    };
    pieChart.setOption(option, true);
  }
}

// 更新增长率图表
function updateGrowthChart() {
  if (!growthChart && growthChartContainer.value) {
    growthChart = echarts.init(growthChartContainer.value);
  }
  if (growthChart) {
    const xAxisData = growthData.value.map(item => item.month);
    const seriesData = growthData.value.map(item => item.growth_rate);
    const option = {
      title: { text: '月度增长率 (%)', left: 'center' },
      tooltip: { trigger: 'axis', formatter: '{b}<br/>增长率: {c}%' },
      xAxis: { type: 'category', data: xAxisData },
      yAxis: { type: 'value', axisLabel: { formatter: '{value} %' } },
      series: [{ name: '增长率', data: seriesData, type: 'line', smooth: true, color: '#ff6347' }]
    };
    growthChart.setOption(option, true);
  }
}

// --- 监听器和生命周期钩子 ---
// 监听筛选条件的变化，并重新获取相关数据
watch([startMonth, endMonth], () => {
  if (!loading.value) { // 避免在首次加载时重复触发
    Promise.all([fetchData(), fetchGrowthData()]);
  }
});

// 监听各个数据源的变化，并自动更新对应的图表
watch(salesData, updateLineChart, { deep: true });
watch(pieChartData, updatePieChart, { deep: true });
watch(growthData, updateGrowthChart, { deep: true });

// 组件首次挂载时，执行初始化操作
onMounted(async () => {
  loading.value = true;
  // 并行获取所有需要的数据
  await Promise.all([fetchData(), fetchKpiData(), fetchGrowthData()]);
  
  // 填充月份选择器（仅一次）
  const fullMonthData = await axios.get('http://127.0.0.1:8000/api/sales');
  allMonths.value = fullMonthData.data.map(item => item.month);
  startMonth.value = allMonths.value[0];
  endMonth.value = allMonths.value[allMonths.value.length - 1];

  loading.value = false;
});
</script>

<template>
  <div class="container">
    <h1>数据分析仪表盘</h1>
    
    <!-- 筛选器区域 -->
    <div class="filters">
      <div class="filter-item">
        <label for="start-month">开始月份: </label>
        <select id="start-month" v-model="startMonth">
          <option v-for="month in allMonths" :key="month" :value="month">{{ month }}</option>
        </select>
      </div>
      <div class="filter-item">
        <label for="end-month">结束月份: </label>
        <select id="end-month" v-model="endMonth">
          <option v-for="month in allMonths" :key="month" :value="month">{{ month }}</option>
        </select>
      </div>
    </div>
    
    <!-- 加载与错误提示 -->
    <div v-if="loading"><p>正在加载数据...</p></div>
    <div v-if="error" class="error"><p>{{ error }}</p></div>
    
    <!-- 主内容区域 -->
    <div v-if="!loading && !error">
      <!-- 数据表格 -->
      <table v-if="salesData.length > 0">
        <thead>
          <tr>
            <th>月份</th>
            <th>销售额 (万元)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in salesData" :key="item.month">
            <td>{{ item.month }}</td>
            <td>{{ item.sales }}</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td><strong>合计</strong></td>
            <td><strong>{{ totalSales }}</strong></td>
          </tr>
        </tfoot>
      </table>
      <p v-else>当前筛选条件下无数据。</p>
      
      <hr class="divider">
      
      <!-- 图表区域 -->
      <div class="charts-wrapper">
        <div ref="lineChartContainer" class="chart-container"></div>
        <div class="sub-charts-container">
          <div ref="pieChartContainer" class="chart-container"></div>
          <div ref="growthChartContainer" class="chart-container"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* 样式部分 */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f4f7f6;
  color: #333;
  margin: 0;
}

.container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 20px 30px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 2rem;
}

.filters {
  display: flex;
  gap: 20px;
  margin-bottom: 25px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 6px;
  justify-content: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-weight: 500;
}

.filter-item select {
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #ccc;
  background-color: white;
  font-size: 14px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

th, td {
  border: 1px solid #e0e0e0;
  padding: 12px 15px;
  text-align: left;
}

thead {
  background-color: #42b983;
  color: white;
}

tbody tr:nth-child(even) {
  background-color: #f9f9f9;
}

tfoot {
  font-weight: bold;
  background-color: #f5f5f5;
}

.error {
  color: #e74c3c;
  text-align: center;
  font-weight: bold;
  padding: 20px;
}

.divider {
  margin: 40px 0;
  border: 0;
  border-top: 1px solid #eee;
}

.charts-wrapper {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.sub-charts-container {
  display: flex; /* 让内部的饼图和增长率图水平排列 */
  gap: 30px;
  flex-wrap: wrap; /* 在小屏幕上允许换行 */
}

.chart-container {
  flex: 1;
  min-width: 320px;
  height: 400px;
}
</style>
