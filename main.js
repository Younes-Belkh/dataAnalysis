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

const sources = ['https://www.agoda.com/en-gb/search?guid=3d2dbfe6-d25b-450a-96e0-0780673b0bd8&lastSearchedCity=9206&asq=u2qcKLxwzRU5NDuxJ0kOF3T91go8JoYYMxAgy8FkBH1BN0lGAtYH25sdXoy34qb9x2luZTbqtbNJ4w5sn96%2BQcypbn0ImTbHvkv38%2BymSjbPRqu81ZaifqvykM%2BuJhcb4paTD5VHq5sFdVCiCn7snjh%2FkURVt8VQM1wpwV3Y8gmaE0ji46E8DEYIXEgVEmfIQYl3V1iy9nb%2B0qxM0R6Qmg%3D%3D&city=1194&tick=639291535680&locale=en-gb&ckuid=c97f86b1-1980-4da0-9960-7289c75bd3cb&prid=0&currency=EUR&correlationId=ac69ff46-c7a8-42a8-a128-cacf27f01362&analyticsSessionId=-5241639957175772908&pageTypeId=1&realLanguageId=16&languageId=1&origin=DZ&stateCode=09&cid=-1&userId=c97f86b1-1980-4da0-9960-7289c75bd3cb&whitelabelid=1&loginLvl=0&storefrontId=3&currencyId=1&currencyCode=EUR&htmlLanguage=en-gb&cultureInfoName=en-gb&machineName=am-pc-4i-cronos-spa-acm-web-7cf9755c9-n75q7&trafficGroupId=4&trafficSubGroupId=4&aid=130243&useFullPageLogin=true&cttp=4&isRealUser=true&mode=production&browserFamily=Chrome&cdnDomain=agoda.net&checkIn=2027-01-01&checkOut=2027-01-31&rooms=1&adults=2&children=0&priceCur=EUR&los=30&textToSearch=Algiers&travellerType=1&familyMode=off&ds=zFat830j8G4MbCv4&sort=agodaRecommended']
const classes = '.afab5-box'
//  afab5-bg-generic-base-transparent afab5-fill-inherit afab5-text-inherit afab5-h-full afab5-cursor-pointer afab5-outline-none afab5-text-start afab5-p-0   afab5-border-0   
// 'https://booking.com', 'https://tripadvisor.com', 'https://trivago.com', 

for (const url of sources) {
    const res = await fetch(url, {
        headers: { 'User-Agent': 'Mozilla/5.0' }
    })

    console.log(url, res.status)          // check this first

    const html = await res.text()         // await the text
    const $ = cheerio.load(html)
    fs.writeFile('agoda.txt', html, (err)=>{
        if(err){
            console.log(`error has happened: ${err}`)
        }
    })

    console.log('h1 count:', $(classes).length)
    $(classes).each((_, el) => {
        // console.log('  h1:', $(el).text().trim())
        
    })
}

