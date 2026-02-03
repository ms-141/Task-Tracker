// javascript listener that checks for when the page had been loaded
document.addEventListener('DOMContentLoaded', function () {
    // creating entities to be used in a function
    const button = document.getElementById('getQuotesBtn');
    const container = document.getElementById('quotesContainer');

    // listener for when the button entity gets pressed (clicked)
    button.addEventListener('click', async function () {
        // Using CORS proxy to bypass certificate issues
        const url = 'https://corsproxy.io/?https://api.quotable.io/quotes/random?limit=3'

        try {
            //save the response to a response object
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error('API request failed');
            }

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

                //adding the new quoteDiv to the quotes container
                container.appendChild(quoteDiv);
            });

        } catch (error) {
            console.error('Error:', error);
            container.innerHTML = '<p style="color:red;">Error loading quotes: ' + error.message + '</p>';
        }
    })


})


})