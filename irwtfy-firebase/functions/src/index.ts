import { Agent } from 'https'
import axios from 'axios'
import { initializeApp, firestore } from 'firebase-admin'
import { config, https } from 'firebase-functions'

initializeApp(config().firebase)

const db = firestore()
const countRef = db.collection('irwtfy').doc('count')
const agent = new Agent({ keepAlive: true })

export const randomEntry = https.onRequest(async (request, response) => {
  const doc = await countRef.get()
  const data = doc.data()
  let count: number
  if (data && data.count && parseInt(data.count) > 0) {
    count = parseInt(data.count)
  } else {
    const countResponse = await axios.get('https://www.blogger.com/feeds/6752139154038265086/posts/default', {
      params: { 'alt': 'json', 'start-index': 1, 'max-results': 1, },
      httpsAgent: agent,
    })
    count = countResponse.data.feed.openSearch$totalResults.$t
    await countRef.set({ count: count })
  }

  const resp = await axios.get('https://www.blogger.com/feeds/6752139154038265086/posts/default', {
    params: { 'alt': 'json', 'start-index': Math.floor(Math.random() * count) + 1, 'max-results': 1, },
    httpsAgent: agent,
  })
  const url = resp.data.feed.entry[0].link.find(l => l.rel === 'alternate').href
  const c = parseInt(resp.data.feed.openSearch$totalResults.$t)

  if (c !== count) {
    await countRef.set({ count: c })
  }

  response.redirect(url)
})
