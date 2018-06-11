import * as https from 'https'
import axios from 'axios'
import * as admin from 'firebase-admin'
import * as functions from 'firebase-functions'

admin.initializeApp(functions.config().firebase)

const db = admin.firestore()
const countRef = db.collection('irwtfy').doc('count')
const agent = new https.Agent({ keepAlive: true })

export const randomEntry = functions.https.onRequest((request, response) => countRef.get()
  .then(doc => {
    if (!doc.exists) {
      console.warn('No stored count!')
      return Promise.reject('no stored count')
    } else {
      return Promise.resolve(doc.data().count)
    }
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
      const c = resp.data.feed.openSearch$totalResults.$t
      if (c !== count) {
        return countRef.set({ count: c }).then(_ => Promise.resolve(url))
      }
      return Promise.resolve(url)
    })
    .then(url => response.redirect(307, url))
  ));
