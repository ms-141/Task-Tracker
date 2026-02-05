// Javascript listener that checks for when the page had been loaded
document.addEventListener('DOMContentLoaded', function () {
    // Creating entities to be used in a function
    const button = document.getElementById('getQuotesBtn');
    const container = document.getElementById('quotesContainer');

    // Listener for when the button entity gets pressed (clicked)
    button.addEventListener('click', async function () {
        // Using GitHub Zen API reliable and always maintained
        const url = 'https://api.github.com/zen'

        // Try catch block in case the API call fails
        try {
            // Clearing previous quotes
            container.innerHTML = '';

            // Fetch zen quote to get the data
            const response = await fetch(url);

            // GitHub Zen returns plain text, not JSON
            const quoteText = await response.text();

            // create HTML elements to add to the page
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

    // Ask for how much free time
    let freeHours;
    const questionFreeTime = document.getElementById('questionFreeTime');
    questionFreeTime.addEventListener('input', function () {
        freeHours = Number(questionFreeTime.value);
    });

    // Ask for upcoming tasks
    let numOfTasks;
    const questionTasks = document.getElementById('questionTasks');
    questionTasks.addEventListener('input', function () {
        numOfTasks = Number(questionTasks.value);
    });

    // How many days until due date
    // let daysRemaining;
    // const 

    // Output daily time 
    let outputNumber;
    const answerContainer = document.getElementById('timePerDayContainer');
    questionTasks.addEventListener('input', function () {
        outputNumber = Math.round((freeHours * 60) / numOfTasks);
        const answerText = document.createElement('p')
        answerText.textContent = 'You should spend ' + outputNumber + ' minutes on each task.'
        answerContainer.appendChild(answerText);
    });


});