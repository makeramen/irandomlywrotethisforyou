import * as admin from 'firebase-admin'
import * as functions from 'firebase-functions'

admin.initializeApp(functions.config().firebase)

const db = admin.firestore()
const countRef = db.collection('irwtfy').doc('count')

export const randomEntry = functions.https.onRequest((request, response) => {
  response.send("Hello from Firebase!");
});
