const { request } = require('../../utils/api')
const app = getApp()

Page({
  data: {
    days: [],
    totalDays: 0,
    loading: false,
    isLoggedIn: false
  },

  onShow() {
    this.checkLoginStatus()
    this.loadCalendar()
  },

  checkLoginStatus() {
    const isLoggedIn = !!app.globalData.user
    this.setData({ isLoggedIn })
  },

  loadCalendar() {
    if (!this.data.isLoggedIn) {
      this.setData({ loading: false, days: [], totalDays: 0 })
      return
    }
    this.setData({ loading: true })
    request('/api/calendar')
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
