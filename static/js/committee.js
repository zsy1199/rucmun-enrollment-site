// 会场详情页面JavaScript

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

// 调整颜色亮度
function adjustBrightness(rgb, percent) {
    const match = rgb.match(/\d+/g);
    if (!match) return rgb;
    const r = Math.max(0, Math.min(255, parseInt(match[0]) + percent));
    const g = Math.max(0, Math.min(255, parseInt(match[1]) + percent));
    const b = Math.max(0, Math.min(255, parseInt(match[2]) + percent));
    return `rgb(${r}, ${g}, ${b})`;
}

// 会场介绍内容：从静态 JSON 读取（static/data/intros.json）

// 从 URL 参数获取会场名称
function getCommitteeNameFromURL() {
    const params = new URLSearchParams(window.location.search);
    const name = params.get('name');
    if (name) {
        return decodeURIComponent(name);
    }
    // 如果没有 query 参数，尝试从 hash 读取
    if (window.location.hash) {
        return decodeURIComponent(window.location.hash.substring(1));
    }
    return null;
}

// 会场列表（需要与 data_processor.py 中的 COMMITTEES 保持一致）
const COMMITTEES = [
    "联合国大会第四委员会",
    "联合国系统联动体系",
    "第二十九届联合国气候变化大会及其临时工作委员会",
    "国际足联球员负荷专责工作组非正式会议",
    "历史谈判委员会",
    "历史联动委员会",
    "UNSC",
    "UNHSP",
    "主新闻中心"
];

// 获取当前会场名称
const committeeName = getCommitteeNameFromURL();

// 加载特定会场的统计数据（从静态 JSON 读取）
async function loadCommitteeStats() {
    if (!committeeName) {
        console.error('未指定会场名称');
        document.getElementById('committeeTitle').textContent = '会场不存在';
        document.getElementById('updateTime').textContent = '请从主页选择会场';
        return;
    }

    // 更新页面标题
    document.getElementById('committeeTitle').textContent = committeeName;

    // 生成其他会场链接
    const committeesList = document.getElementById('committeesList');
    if (committeesList) {
        committeesList.innerHTML = COMMITTEES
            .filter(c => c !== committeeName)
            .map(c => `<a href="/committee.html?name=${encodeURIComponent(c)}" class="committee-link">${c}</a>`)
            .join('');
    }

    try {
        const response = await fetch('/data/stats.json', { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const result = await response.json();

        const allStats = result.committees || {};
        const updateTime = result.update_time || '';
        const data = allStats[committeeName];

        if (updateTime) {
            document.getElementById('updateTime').textContent = `数据更新时间: ${updateTime}`;
        } else {
            document.getElementById('updateTime').textContent = '数据更新时间: 未知';
        }

        if (data) {
            // 更新容量信息
            const capacity = data.capacity || 0;
            const ratio = data.ratio || 0;
            document.getElementById('capacity').textContent = capacity;

            // 根据比例设置热力图颜色
            const capacityCard = document.getElementById('capacityCard');
            const heatmapColor = getHeatmapColor(ratio);
            capacityCard.style.background = `linear-gradient(135deg, ${heatmapColor} 0%, ${adjustBrightness(heatmapColor, -20)} 100%)`;
        } else {
            console.warn(`未找到会场 ${committeeName} 的统计数据`);
            document.getElementById('capacity').textContent = '-';
        }

        // 更新会场介绍（无论数据是否存在）
        updateIntroduction();
    } catch (error) {
        console.error('加载静态统计数据失败:', error);
        document.getElementById('updateTime').textContent = '数据加载失败';
        // 即使请求失败，也尝试显示介绍
        updateIntroduction();
    }
}

// 更新会场介绍内容
function updateIntroduction() {
    try {
        const introContent = document.getElementById('introContent');
        if (!introContent) {
            console.error('找不到introContent元素');
            return;
        }
        
        // 确保committeeName已定义
        if (!committeeName) {
            console.error('committeeName未定义');
            introContent.textContent = '该会场的详细介绍信息待补充。';
            return;
        }

        fetch('/data/intros.json', { cache: 'no-store' })
            .then((res) => res.json())
            .then((json) => {
                if (!json) {
                    introContent.textContent = '该会场的详细介绍信息待补充。';
                    return;
                }
                const content = json[committeeName];
                if (!content) {
                    console.warn(`未找到会场 "${committeeName}" 的介绍`);
                    introContent.textContent = '该会场的详细介绍信息待补充。';
                    return;
                }
                const raw = String(content).replace(/\r\n/g, '\n');

                // 安全转义（防止txt中包含HTML被执行）
                const escapeHtml = (s) =>
                    s
                        .replace(/&/g, '&amp;')
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;');

                const escaped = escapeHtml(raw);

                // 加粗字段名（中文 + 英文常见字段）
                const labels = [
                    '委员会',
                    '议题',
                    '会场容量',
                    '工作语言',
                    '议事规则',
                    '主席团负责人',
                    '会场介绍',
                    'Committee',
                    'Topic',
                    'Total number of delegates',
                    'Language',
                    'Rules of Procedure',
                    'Dais Head',
                    'Introduction',
                ];

                // 在任意位置命中 “label:” 或 “label：” 都加粗 label+冒号
                const labelPattern = new RegExp(
                    `(${labels.map((l) => l.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')).join('|')})([:：])`,
                    'g'
                );

                const withBoldLabels = escaped.replace(labelPattern, '<strong>$1$2</strong>');

                // 换行显示：配合 pre-wrap 也可以，但 <br> 更稳定
                introContent.innerHTML = withBoldLabels.replace(/\n/g, '<br>');
            })
            .catch((e) => {
                console.error('拉取会场介绍失败:', e);
                introContent.textContent = '该会场的详细介绍信息待补充。';
            });
    } catch (error) {
        console.error('更新介绍时出错:', error);
        const introContent = document.getElementById('introContent');
        if (introContent) {
            introContent.textContent = '该会场的详细介绍信息待补充。';
        }
    }
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', function() {
    // 立即显示介绍内容，不等待API响应
    updateIntroduction();
    // 然后加载统计数据
    loadCommitteeStats();
});

// 每30秒自动刷新数据
setInterval(loadCommitteeStats, 30000);

