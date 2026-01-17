// 格式化日期函数
export const formatDate = (dateStr) => {
    if (!dateStr) return '无'
    const date = new Date(dateStr)
    const year = date.getFullYear()
    const month = date.getMonth() + 1
    const day = date.getDate()
    const hour = date.getHours().toString().padStart(2, '0')
    const minute = date.getMinutes().toString().padStart(2, '0')
    const second = date.getSeconds().toString().padStart(2, '0')
    return `${year}年${month}月${day}日 ${hour}:${minute}:${second}`
}

// 限制小数位数函数
export function limitDecimalPlaces(value, decimalPlaces = 2) {
    if (value) {
        // 保留最多两位小数
        return Number(parseFloat(value).toFixed(decimalPlaces));
    }
    return value; // 如果值为空，返回原值
}

// 格式化为ISO字符串（本地时间）
export const formatToISO = (dateStr) => {
    if (!dateStr) return null
    const date = new Date(dateStr)
    const offset = date.getTimezoneOffset() * 60000
    const localDate = new Date(date.getTime() - offset)
    return localDate.toISOString().slice(0, 19)
}
