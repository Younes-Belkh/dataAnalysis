
import fetch from './javascript/fetch.js'
import clean from './javascript/clean.js'


console.log(`------- STAGE 1: FETCHING DATA -------`)
await fetch()


console.log(`------- STAGE 2: CLEANING TO CSV -------`)
await clean()



console.log(`------- DONE! -------`)