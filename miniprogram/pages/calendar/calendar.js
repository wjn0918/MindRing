const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    days: [],
    totalDays: 0,
    loading: false
  },

  onShow() {
    this.loadCalendar()
  },

  loadCalendar() {
    this.setData({ loading: true })
    request('/api/calendar', { query: { user_id: app.globalData.user.id } })
      .then((days) => {
        const mapped = days
          .slice()
          .reverse()
          .map((day) => ({
            ...day,
            level: Math.min(3, day.count)
          }))
        this.setData({ days: mapped, totalDays: days.length })
      })
      .catch((error) => wx.showToast({ title: error.message, icon: 'none' }))
      .finally(() => this.setData({ loading: false }))
  }
})
