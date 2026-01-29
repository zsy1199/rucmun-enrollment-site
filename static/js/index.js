// 主页面JavaScript

// 根据比例计算热力图颜色（0-1之间，可能超过1）
function getHeatmapColor(ratio) {
    // 将比例限制在0-1.5之间进行颜色映射
    const normalizedRatio = Math.min(ratio, 1.5) / 1.5;
    
    // 从蓝色（低）到橙色（高）的渐变
    // 0.0 -> 蓝色 (59, 130, 246) - 浅蓝
    // 0.5 -> 青色 (34, 211, 238) - 青蓝
    // 1.0 -> 橙色 (249, 115, 22) - 橙色
    
    let r, g, b;
    
    if (normalizedRatio < 0.5) {
        // 蓝色到青蓝色
        const t = normalizedRatio * 2;
        r = Math.round(59 + (34 - 59) * t);
        g = Math.round(130 + (211 - 130) * t);
        b = Math.round(246 + (238 - 246) * t);
    } else {
        // 青蓝色到橙色
        const t = (normalizedRatio - 0.5) * 2;
        r = Math.round(34 + (249 - 34) * t);
        g = Math.round(211 + (115 - 211) * t);
        b = Math.round(238 + (22 - 238) * t);
    }
    
    return `rgb(${r}, ${g}, ${b})`;
}

// 加载统计数据（从静态 JSON 读取）
async function loadStats() {
    try {
        const response = await fetch('/static/data/stats.json', { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const result = await response.json();

        const stats = result.committees || {};
        const updateTime = result.update_time || '';
        
        // 更新更新时间
        if (updateTime) {
            document.getElementById('updateTime').textContent = `数据更新时间: ${updateTime}`;
        } else {
            document.getElementById('updateTime').textContent = '数据更新时间: 未知';
        }
        
        // 更新每个会场的预览
        const committeeCards = document.querySelectorAll('.committee-card');
        const committees = Array.from(committeeCards).map((card) => {
            return card.querySelector('h3').textContent;
        });
        
        committees.forEach((committee, index) => {
            const cardEl = committeeCards[index];
            const previewEl = document.getElementById(`preview-${index}`);
            const data = stats[committee];

            if (data) {
                const capacity = data.capacity || 0;
                const ratio = data.ratio || 0;
                
                // 显示容量（不展示任何志愿相关信息）
                previewEl.innerHTML = `
                    <p><strong>会场容量: ${capacity}</strong></p>
                `;
                
                // 根据比例设置热力图颜色（蓝色到橙色）
                const heatmapColor = getHeatmapColor(ratio);
                cardEl.style.background = `linear-gradient(135deg, ${heatmapColor} 0%, ${adjustBrightness(heatmapColor, -20)} 100%)`;
                // 统一使用白色文字
                cardEl.style.color = 'white';
            } else {
                previewEl.innerHTML = '<p>暂无数据</p>';
                cardEl.style.background = 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)';
                cardEl.style.color = 'white';
            }
        });
    } catch (error) {
        console.error('加载静态数据失败:', error);
        document.getElementById('updateTime').textContent = '数据加载失败';
    }
}

// 调整颜色亮度
function adjustBrightness(rgb, percent) {
    const match = rgb.match(/\d+/g);
    if (!match) return rgb;
    const r = Math.max(0, Math.min(255, parseInt(match[0]) + percent));
    const g = Math.max(0, Math.min(255, parseInt(match[1]) + percent));
    const b = Math.max(0, Math.min(255, parseInt(match[2]) + percent));
    return `rgb(${r}, ${g}, ${b})`;
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', loadStats);

// 每30秒自动刷新数据
setInterval(loadStats, 30000);

