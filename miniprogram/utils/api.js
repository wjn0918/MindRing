const app = getApp()

function getToken() {
  return wx.getStorageSync('mindring_token')
}

function buildUrl(path, query) {
  const baseUrl = app.globalData.apiBaseUrl.replace(/\/$/, '')
  const queryString = query
    ? Object.keys(query)
        .filter((key) => query[key] !== undefined && query[key] !== null && query[key] !== '')
        .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(query[key])}`)
        .join('&')
    : ''
  return `${baseUrl}${path}${queryString ? `?${queryString}` : ''}`
}

function request(path, options = {}) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    wx.request({
      url: buildUrl(path, options.query),
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
          return
        }
        reject(new Error(res.data && res.data.detail ? res.data.detail : '请求失败'))
      },
      fail(error) {
        reject(error)
      }
    })
  })
}

module.exports = {
  request,
  buildUrl
}
