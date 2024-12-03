class AKTAWorksheetCreator {
    constructor(data) {
      this.rows = data.rows;
      this.chart = null;
      this.cv = data.cv; // cv の初期値を設定
  
      this.initializeEventListeners();
      this.renderTable();
      this.renderChart();
    }
  
    initializeEventListeners() {
      document.getElementById('add-row').addEventListener('click', () => this.addRow());
      document.getElementById('delete-row').addEventListener('click', () => this.deleteLastRow());
      document.getElementById('column-cv').addEventListener('change', () => {
        this.cv = parseFloat(document.getElementById('column-cv').value); // cv の値を更新
        this.getTotalTime();
        this.updateChart(); // cv の変更時にグラフを更新
      });
    }
  
    addRow() {
      this.rows.push({ rate: 0, length: 0, percentB: 0, slopeType: 'step', path: '', fractionVol: 0 });
      this.renderTable();
      this.updateChart();
    }
  
    deleteLastRow() {
      if (this.rows.length > 1) {
        this.rows.pop();
        this.renderTable();
        this.updateChart();
      }
    }
  
    getLineColor(path) {
      switch (path) {
        case "sample loop":
          return "red";
        case "sample pump":
          return "green";
        default:
          return "#8884d8";
      }
    }
  
    renderTable() {
      const tbody = document.querySelector('#program-table tbody');
      if (!tbody) return;
  
      tbody.innerHTML = '';
      this.rows.forEach((row, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="px-2 py-4 whitespace-nowrap w-24"><input type="number" name="rate[]" value="${row.rate}" class="w-full px-2 py-1 border rounded" data-index="${index}" data-field="rate"></td>
          <td class="px-2 py-4 whitespace-nowrap w-24"><input type="number" name="length[]" value="${row.length}" class="w-full px-2 py-1 border rounded" data-index="${index}" data-field="length"></td>
          <td class="px-2 py-4 whitespace-nowrap w-24"><input type="number" name="percentB[]" value="${row.percentB}" class="w-full px-2 py-1 border rounded" data-index="${index}" data-field="percentB"></td>
          <td class="px-2 py-4 whitespace-nowrap w-50">
            <select name="slopeType[]" class="w-full px-2 py-1 border rounded" data-index="${index}" data-field="slopeType">
              <option value="step" ${row.slopeType === 'step' ? 'selected' : ''}>step</option>
              <option value="gradient" ${row.slopeType === 'gradient' ? 'selected' : ''}>gradient</option>
            </select>
          </td>
          <td class="px-2 py-4 whitespace-nowrap w-50">
            <select name="path[]" class="w-full px-2 py-1 border rounded" data-index="${index}" data-field="path">
              <option value="" ${row.path === '' ? 'selected' : ''}>-</option>
              <option value="sample loop" ${row.path === 'sample loop' ? 'selected' : ''}>sample loop</option>
              <option value="sample pump" ${row.path === 'sample pump' ? 'selected' : ''}>sample pump</option>
            </select>
          </td>
          <td class="px-1 py-4 whitespace-nowrap w-24"><input type="number" name="fractionVol[]" value="${row.fractionVol}" class="w-full px-1 py-1 border rounded" data-index="${index}" data-field="fractionVol"></td>
        `;
        tbody.appendChild(tr);
      });
  
      tbody.addEventListener('change', (e) => {
        this.handleTableChange(e);
        this.getTotalTime();
      });
    }
  
    handleTableChange(e) {
      const target = e.target;
      const index = parseInt(target.dataset.index);
      const field = target.dataset.field;
  
      if (!isNaN(index) && field) {
        if (field === 'slopeType' || field === 'path' || field === 'fractionVol') {
          this.rows[index][field] = target.value;
        } else {
          this.rows[index][field] = parseFloat(target.value);
        }
        this.updateChart();
      }
    }
  
    getborderColor_context = (context) => {
      const index = context.p0DataIndex;
      const chartData = this.getChartData();
      return this.getLineColor(chartData[index].path);
    }
  
    renderChart() {
      const ctx = document.getElementById('gradient-chart');
      if (!ctx) return;
  
      const chartData = this.getChartData();
  
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {
          datasets: [{
            label: '%B',
            data: chartData,
            borderColor: '#8884d8',
            borderWidth: 2,
            fill: false,
            stepped: false,
            segment: {
              borderColor: this.getborderColor_context,
            }
          }
        ]
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'linear',
              title: {
                display: true,
                text: '溶出量 (CV)'
              }
            },
            y: {
              title: {
                display: true,
                text: '%B'
              },
              min: -5,
              max: 105
            }
          },
          plugins: {
            
            // 塗りつぶし用のプラグインを追加
            filler: {
              propagate: false // 隣接するデータセットに塗りつぶしを適用しない
            },
            legend: {
                display: false
            }
        }
    }
      });
    }

    getFracDataset() {
        let fracdata = [];
        let cumulativeLength = 0;

        this.rows.forEach((row, index)=>{
            
            if (parseFloat(row.fractionVol) != 0) {
                const frac_cv = parseFloat(row.fractionVol) / parseFloat(this.cv);
                
                const frac_n = Math.ceil(row.length/frac_cv);
                console.log(frac_n)
                for (let i = 1; i <= frac_n; i++) {
                    fracdata.push(
                        [{ x: cumulativeLength, y: 0},
                        { x: cumulativeLength, y: 100},
                        { x: cumulativeLength+frac_cv, y: 100},
                        { x: cumulativeLength+frac_cv, y: 0}]);
                    cumulativeLength += frac_cv;
                }
            }else {
                cumulativeLength += row.length;
            }    
        });
        
        let fracdataset = [];
        fracdata.forEach((data,index)=>{
            fracdataset.push(
                {
                    type:'line',
                    label: 'Fill Area',
                    data: data,
                    //borderColor: 'rgba(255, 99, 132, 0.2)', // 透明度の低い色
                    //backgroundColor: 'rgba(255, 99, 132, 0.05)',
                    fill: true, // 塗りつぶしを有効にする
                    borderWidth: 1 // ボーダーを非表示にする
                    
                  }
            );
        });

        return fracdataset;
    }

  
    updateChart() {
      const chartData = this.getChartData();
      const fracdataset = this.getFracDataset(chartData);
  
      const segment = {
        borderColor: this.getborderColor_context,
      }
  
      if (this.chart) {
        this.chart.data.datasets[0].data = chartData;
        let dataset_len = this.chart.data.datasets.length

        if (this.chart.data.datasets.length >1) {
            for (let i = 0; i < dataset_len-1; i++) {
                this.chart.data.datasets.pop();
            }
        }
        fracdataset.forEach((data,index)=> {
            this.chart.data.datasets.push(data);
        });

        this.chart.data.datasets[0].segment = segment;

        this.chart.update();
      }
    }
  
    getChartData() {
      let cumulativeLength = 0;
      let chartData = [];
      let data_len = 0
  
      this.rows.forEach((row, index) => {
        const startLength = cumulativeLength;
  
        cumulativeLength += row.length;

        if (index == 0) {
            chartData.push({ x: startLength, y: row.percentB, path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
            chartData.push({ x: cumulativeLength, y: row.percentB, path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
            data_len += 2
        }else if (row.slopeType == 'step') {
            chartData.push({ x: startLength, y: row.percentB, path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
            chartData.push({ x: cumulativeLength, y: row.percentB, path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
            data_len += 2
        } else if (row.slopeType == "gradient") {
          chartData[data_len-1]["path"] = row.path;
          chartData[data_len-1]["fractionvol"] = row.fractionVol;
          chartData.push({ x: cumulativeLength, y: row.percentB, path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
          data_len += 1
        }
   
      });
  
      return chartData;
    }
  
    getTotalTime() {
      let totalTime = 0;
  
      this.rows.forEach(row => {
        totalTime += this.cv * row.rate * row.length; // 流速と長さの積を合計する
      });
  
      const totalTimeElement = document.getElementById('total-time');
      if (totalTimeElement) {
        totalTimeElement.textContent = `合計時間: ${totalTime.toFixed(2)} min`;
      }
    }
  }
  

  function getChartData(rows, cv) {
    let cumulativeLength = 0;
    let chartData = [];
    let data_len = 0;

    rows.forEach((row, index) => {
      const startLength = cumulativeLength;

      cumulativeLength += parseFloat(row.length);

      if (index == 0) {
        chartData.push({ x: startLength, y: parseFloat(row.percentB), path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
        chartData.push({ x: cumulativeLength, y: parseFloat(row.percentB), path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
        data_len += 2
      } else if (row.slopeType == 'step') {
        chartData.push({ x: startLength, y: parseFloat(row.percentB), path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
        chartData.push({ x: cumulativeLength, y: parseFloat(row.percentB), path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
        data_len += 2
      } else if (row.slopeType == "gradient") {
        chartData[data_len - 1]["path"] = row.path;
        chartData[data_len - 1]["fractionvol"] = row.fractionVol;
        chartData.push({ x: cumulativeLength, y: parseFloat(row.percentB), path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
        data_len += 1
      }

    });

    return chartData;
  }





  class AKTAWorksheetCreator2 {
    constructor(data) {
      this.rows = data.rows;
      this.chart = null;
      this.cv = data.cv; // cv の初期値を設定
  
      this.updateChart()
      this.renderChart();
    }
  
  
    getLineColor(path) {
      switch (path) {
        case "sample loop":
          return "red";
        case "sample pump":
          return "green";
        default:
          return "#8884d8";
      }
    }
  
  

    getborderColor_context = (context) => {
      const index = context.p0DataIndex;
      const chartData = this.getChartData();
      return this.getLineColor(chartData[index].path);
    }
  
    renderChart() {
      const ctx = document.getElementById('gradient-chart');
      if (!ctx) return;
  
      const chartData = this.getChartData();
  
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {
          datasets: [{
            label: '%B',
            data: chartData,
            borderColor: '#8884d8',
            borderWidth: 2,
            fill: false,
            stepped: false,
            segment: {
              borderColor: this.getborderColor_context,
            }
          }
        ]
        },
        options: {
          responsive: true,
          scales: {
            x: {
              type: 'linear',
              title: {
                display: true,
                text: '溶出量 (CV)'
              }
            },
            y: {
              title: {
                display: true,
                text: '%B'
              },
              min: -5,
              max: 105
            }
          },
          plugins: {
            
            // 塗りつぶし用のプラグインを追加
            filler: {
              propagate: false // 隣接するデータセットに塗りつぶしを適用しない
            },
            legend: {
                display: false
            }
        }
    }
      });
    }

    getFracDataset() {
        let fracdata = [];
        let cumulativeLength = 0;

        this.rows.forEach((row, index)=>{
            
            if (parseFloat(row.fractionVol) != 0) {
                const frac_cv = parseFloat(row.fractionVol) / parseFloat(this.cv);
                
                const frac_n = Math.ceil(row.length/frac_cv);
                console.log(frac_n)
                for (let i = 1; i <= frac_n; i++) {
                    fracdata.push(
                        [{ x: cumulativeLength, y: 0},
                        { x: cumulativeLength, y: 100},
                        { x: cumulativeLength+frac_cv, y: 100},
                        { x: cumulativeLength+frac_cv, y: 0}]);
                    cumulativeLength += frac_cv;
                }
            }else {
                cumulativeLength += row.length;
            }    
        });
        
        let fracdataset = [];
        fracdata.forEach((data,index)=>{
            fracdataset.push(
                {
                    type:'line',
                    label: 'Fill Area',
                    data: data,
                    //borderColor: 'rgba(255, 99, 132, 0.2)', // 透明度の低い色
                    //backgroundColor: 'rgba(255, 99, 132, 0.05)',
                    fill: true, // 塗りつぶしを有効にする
                    borderWidth: 1 // ボーダーを非表示にする
                    
                  }
            );
        });

        return fracdataset;
    }

  
    updateChart() {
      const chartData = this.getChartData();
      const fracdataset = this.getFracDataset(chartData);
  
      const segment = {
        borderColor: this.getborderColor_context,
      }
  
      if (this.chart) {
        this.chart.data.datasets[0].data = chartData;
        let dataset_len = this.chart.data.datasets.length

        if (this.chart.data.datasets.length >1) {
            for (let i = 0; i < dataset_len-1; i++) {
                this.chart.data.datasets.pop();
            }
        }
        fracdataset.forEach((data,index)=> {
            this.chart.data.datasets.push(data);
        });

        this.chart.data.datasets[0].segment = segment;

        this.chart.update();
      }
    }
  
    getChartData() {
      let cumulativeLength = 0;
      let chartData = [];
      let data_len = 0
  
      this.rows.forEach((row, index) => {
        const startLength = cumulativeLength;
  
        cumulativeLength += row.length;

        if (index == 0) {
            chartData.push({ x: startLength, y: row.percentB, path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
            chartData.push({ x: cumulativeLength, y: row.percentB, path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
            data_len += 2
        }else if (row.slopeType == 'step') {
            chartData.push({ x: startLength, y: row.percentB, path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
            chartData.push({ x: cumulativeLength, y: row.percentB, path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
            data_len += 2
        } else if (row.slopeType == "gradient") {
          chartData[data_len-1]["path"] = row.path;
          chartData[data_len-1]["fractionvol"] = row.fractionVol;
          chartData.push({ x: cumulativeLength, y: row.percentB, path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
          data_len += 1
        }
   
      });
  
      return chartData;
    }
  
    getTotalTime() {
      let totalTime = 0;
  
      this.rows.forEach(row => {
        totalTime += this.cv * row.rate * row.length; // 流速と長さの積を合計する
      });
  
      const totalTimeElement = document.getElementById('total-time');
      if (totalTimeElement) {
        totalTimeElement.textContent = `合計時間: ${totalTime.toFixed(2)} min`;
      }
    }
  }
  

  function getChartData(rows, cv) {
    let cumulativeLength = 0;
    let chartData = [];
    let data_len = 0;

    rows.forEach((row, index) => {
      const startLength = cumulativeLength;

      cumulativeLength += parseFloat(row.length);

      if (index == 0) {
        chartData.push({ x: startLength, y: parseFloat(row.percentB), path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
        chartData.push({ x: cumulativeLength, y: parseFloat(row.percentB), path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
        data_len += 2
      } else if (row.slopeType == 'step') {
        chartData.push({ x: startLength, y: parseFloat(row.percentB), path: row.path, slopetype: row.slopeType, fractionvol: row.fractionVol });
        chartData.push({ x: cumulativeLength, y: parseFloat(row.percentB), path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
        data_len += 2
      } else if (row.slopeType == "gradient") {
        chartData[data_len - 1]["path"] = row.path;
        chartData[data_len - 1]["fractionvol"] = row.fractionVol;
        chartData.push({ x: cumulativeLength, y: parseFloat(row.percentB), path: "", slopetype: row.slopeType, fractionvol: row.fractionVol });
        data_len += 1
      }

    });

    return chartData;
  }