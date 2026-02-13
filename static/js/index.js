// 主页面JavaScript

// 会场名称到图片文件名的映射
const COMMITTEE_IMAGE_MAP = {
    "联合国大会第四委员会": "联合国大会第四委员会.jpg",
    "联合国系统联动体系": "联合国系统联动.jpg",
    "第二十九届联合国气候变化大会及其临时工作委员会": "第二十九届联合国气候变化大会临时工作委员会.jpg",
    "国际足联球员负荷专责工作组非正式会议": "国际足联球员负荷专责工作组非正式会议.jpg",
    "历史谈判委员会": "历史谈判委员会.jpg",
    "历史联动委员会": "历史联动委员会.jpg",
    "United Nations Security Council": "UNSC.jpg",
    "United Nations Human Settlements Programme": "UNHSP.jpg",
    "主新闻中心": "主新闻中心.jpg"
};

// 根据比例计算热力图颜色（0-1之间，可能超过1）
function getHeatmapColor(ratio) {
    // 放大低比例段的映射，使变色更明显：ratio * 3 封顶 1，约 0.33 即满橙
    const normalizedRatio = Math.min(1, ratio * 3);
    
    // 从深蓝（低）到橙红（高），对比更强
    // 0.0 -> 深蓝 (30, 64, 180)
    // 0.5 -> 青 (20, 180, 200)
    // 1.0 -> 橙红 (220, 70, 20)
    
    let r, g, b;
    
    if (normalizedRatio < 0.5) {
        const t = normalizedRatio * 2;
        r = Math.round(30 + (20 - 30) * t);
        g = Math.round(64 + (180 - 64) * t);
        b = Math.round(180 + (200 - 180) * t);
    } else {
        const t = (normalizedRatio - 0.5) * 2;
        r = Math.round(20 + (220 - 20) * t);
        g = Math.round(180 + (70 - 180) * t);
        b = Math.round(200 + (20 - 200) * t);
    }
    
    return `rgb(${r}, ${g}, ${b})`;
}

// 加载统计数据（从静态 JSON 读取）
async function loadStats() {
    try {
        // 在 Cloudflare Pages 上，构建输出目录为 static，
        // 其中的内容会被当作站点根目录提供，因此这里用 /data/...
        const response = await fetch('/data/stats.json', { cache: 'no-store' });
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

            // 更新卡片链接
            const encodedName = encodeURIComponent(committee);
            cardEl.onclick = () => {
                window.location.href = `/committee.html?name=${encodedName}`;
            };

            if (data) {
                const capacity = data.capacity || 0;
                const ratio = data.ratio || 0;
                
                // 显示容量（不展示任何志愿相关信息）
                previewEl.innerHTML = `
                    <p><strong>会场容量: ${capacity}</strong></p>
                `;
                
                // 根据比例设置热力图颜色（蓝色到橙色）
                const heatmapColor = getHeatmapColor(ratio);
                
                // 获取对应的背景图片
                const imageFile = COMMITTEE_IMAGE_MAP[committee];
                if (imageFile) {
                    // 设置背景图片和颜色叠加
                    const imageUrl = `/images/committees/${encodeURIComponent(imageFile)}`;
                    const rgbValues = heatmapColor.match(/\d+/g);
                    const darkerRgbValues = adjustBrightness(heatmapColor, -20).match(/\d+/g);
                    // 使用多层背景：颜色渐变叠加在图片上（注意顺序：上面的层先写）
                    cardEl.style.background = `
                        linear-gradient(135deg, rgba(${rgbValues[0]}, ${rgbValues[1]}, ${rgbValues[2]}, 0.7) 0%, rgba(${darkerRgbValues[0]}, ${darkerRgbValues[1]}, ${darkerRgbValues[2]}, 0.7) 100%),
                        url('${imageUrl}')
                    `;
                    cardEl.style.backgroundSize = 'cover';
                    cardEl.style.backgroundPosition = 'center';
                    cardEl.style.backgroundRepeat = 'no-repeat';
                } else {
                    // 如果没有图片，只使用颜色渐变
                    cardEl.style.background = `linear-gradient(135deg, ${heatmapColor} 0%, ${adjustBrightness(heatmapColor, -20)} 100%)`;
                    cardEl.style.backgroundSize = '';
                    cardEl.style.backgroundPosition = '';
                    cardEl.style.backgroundRepeat = '';
                }
                // 统一使用白色文字
                cardEl.style.color = 'white';
                // 进度条：与图例条同款渐变，填充长度表示报名占比（ratio*3 封顶 100%）
                const container = cardEl.parentElement;
                const barFill = container && container.querySelector('.committee-ratio-bar-fill');
                if (barFill) {
                    const fillPercent = Math.min(100, ratio * 3 * 100);
                    barFill.style.width = fillPercent + '%';
                    barFill.style.background = ''; /* 使用 CSS 中定义的渐变 */
                }
            } else {
                previewEl.innerHTML = '<p>暂无数据</p>';
                cardEl.style.background = 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)';
                cardEl.style.color = 'white';
                const container = cardEl.parentElement;
                const barFill = container && container.querySelector('.committee-ratio-bar-fill');
                if (barFill) {
                    barFill.style.width = '0%';
                    barFill.style.background = '#94a3b8';
                }
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

