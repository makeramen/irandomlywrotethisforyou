import { Agent } from 'https'
import axios from 'axios'
import { initializeApp, firestore} from 'firebase-admin'
import { config, https } from 'firebase-functions'

initializeApp(config().firebase)

const db = firestore()
const countRef = db.collection('irwtfy').doc('count')
const agent = new Agent({ keepAlive: true })

export const randomEntry = https.onRequest((request, response) => countRef.get()
  .then(doc => {
    if (doc.exists && 'count' in doc.data()) {
      const count = parseInt(doc.data().count)
      if (typeof count === 'number' && count % 1 === 0) {
        return Promise.resolve(doc.data().count)
      }
      console.log('Store count is bad format!')
      return Promise.reject(undefined)
    }
    console.log('No stored count!')
    return Promise.reject(undefined)
  })
  .catch(err => axios
    .get('https://www.blogger.com/feeds/6752139154038265086/posts/default', {
      params: {
        'alt': 'json',
        'start-index': 1,
        'max-results': 1,
      },
      httpsAgent: agent,
    })
    .then(resp => {
      const c = resp.data.feed.openSearch$totalResults.$t
      return countRef.set({ count: c }).then(_ => Promise.resolve(c))
    }))
  .then(count => axios
    .get('https://www.blogger.com/feeds/6752139154038265086/posts/default', {
      params: {
        'alt': 'json',
        'start-index': Math.floor(Math.random() * count) + 1,
        'max-results': 1,
      },
      httpsAgent: agent,
    })
    .then(resp => {
      const url = resp.data.feed.entry[0].link.find(l => l.rel === 'alternate').href
      const c = parseInt(resp.data.feed.openSearch$totalResults.$t)
      if (c !== count) {
        return countRef.set({ count: c }).then(_ => Promise.resolve(url))
      }
      return Promise.resolve(url)
    })
    .then(url => response.redirect(307, url))
  ));
