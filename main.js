// import * as cheerio from 'cheerio'

// const sources = ['https://booking.com', 'https://tripadvisor.com', 'https://trivago.com', 'https://agoda.com']
// const fetchResults = []
// let fetchResult
// // const keywords = []

// for(let i = 0; i < sources.length; i++){
//     fetchResult = await fetch(sources[i], {
//         headers: {'User-Agent': 'Mozilla/5.0'}
//     })
//     await fetchResults.push(fetchResult)
// }

// const forchResultsStrings = []
// fetchResults.forEach(element=>{
//     const textElement = element.text()
//     const parsed = cheerio.load(textElement)
//     console.log(parsed('h1'))
// })

import * as cheerio from 'cheerio'
import * as fs from 'fs'

const sources = ['https://agoda.com/']
// const classes = '.afab5-box'
//  afab5-bg-generic-base-transparent afab5-fill-inherit afab5-text-inherit afab5-h-full afab5-cursor-pointer afab5-outline-none afab5-text-start afab5-p-0   afab5-border-0   
// 'https://booking.com', 'https://tripadvisor.com', 'https://trivago.com', 

for (const url of sources) {
    const res = await fetch(url, {
        headers:{
            
        }
    })

    console.log(url, res.status)          // check this first

    const html = await res.text()         // await the text
    const $ = cheerio.load(html)
    fs.writeFile('agoda.html', html, (err)=>{
        if(err){
            console.log(`error has happened: ${err}`)
        }
    })

    console.log('h1 count:', $(classes).length)
    $(classes).each((_, el) => {
        // console.log('  h1:', $(el).text().trim())
        
    })
}

