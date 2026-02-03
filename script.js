// javascript listener that checks for when the page had been loaded
document.addEventListener('DOMContentLoaded', function () {
    // creating entities to be used in a function
    const button = document.getElementById('getQuotesBtn');
    const container = document.getElementById('quotesContainer');

    // listener for when the button entity gets pressed (clicked)
    button.addEventListener('click', async function () {
        // create a url object for the endpoint URL
        const url = 'https://api.quotable.io/quotes/random?limit=3'

        //save the response to a response object
        const response = await fetch(url);

        // make a try block in the future

        // make object to receive the response from the api call
        const quotes = await response.json();

        // clearing previous quotes (can get new quotes without refreshing page)
        container.innerHTML = '';

        // loop over array of quotes
        //iterating and creating markup
        quotes.forEach((quoteObj) => {
            //creating HTML elements to add to the page
            const quoteDiv = document.createElement('div');
            const quote = document.createElement('p');

            //quoteObj.content and author use JSON formatting
            quote.textContent = '"' + quoteObj.content + '" - ' + quoteObj.author;

            //adding quote into the quoteDiv
            quoteDiv.appendChild(quote);

            //adding the new quoteDiv to the quotes 
            container.appendChild(quoteDiv);
        })


    })


})