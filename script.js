// javascript listener that checks for when the page had been loaded
document.addEventListener('DOMContentLoaded', function () {
    // creating entities to be used in a function
    const button = document.getElementById('getQuotesBtn');
    const container = document.getElementById('quotesContainer');

    // listener for when the button entity gets pressed (clicked)
    button.addEventListener('click', async function () {
        // Using GitHub Zen API - reliable and always maintained
        const url = 'https://api.github.com/zen'

        try {
            // clearing previous quotes
            container.innerHTML = '';

            // Fetch 3 different zen quotes by calling the API 3 times

            const response = await fetch(url);


            // GitHub Zen returns plain text, not JSON
            const quoteText = await response.text();

            // Create HTML elements to add to the page
            const quoteDiv = document.createElement('div');
            const quote = document.createElement('p');

            quote.textContent = '"' + quoteText + '" - GitHub Zen';

            // Adding quote into the quoteDiv
            quoteDiv.appendChild(quote);

            // Adding the new quoteDiv to the quotes container
            container.appendChild(quoteDiv);

        } catch (error) {
            console.error('Error:', error);
            container.innerHTML = 'Error loading quotes: ' + error.message + '</p>';
        }
    })


});