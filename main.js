//to start this script you can do it 2 ways:
//1- simplest way is to just start an html template that requires this
//  file as it's scipt sourse 
// (i might add one later if i remember, 
// too lazy to search how to exclude an html since i have *.html in .gitignore for client side rendered website fetching)



//2- install node (if you don't already) 
// cd into /javascript of this folder and run 'npm install'
//  no need for node init, because package.json is already there with all what's needed
//  then just go back the root of this project '/dataAnalisis' and fun 'node main'


import fetch from './javascript/fetch.js'
import clean from './javascript/clean.js'


console.log(`------- STAGE 1: FETCHING DATA -------`)
await fetch()


console.log(`------- STAGE 2: CLEANING TO CSV -------`)
await clean()



console.log(`------- DONE! -------`)