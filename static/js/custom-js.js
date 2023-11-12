const div = document.getElementById('myDiv');

div.style.opacity = 1;

setTimeout(() => {
  // Set the opacity of the element to 1.
  div.style.opacity = 1;

  // Use the setInterval() function to gradually decrease the opacity of the element over time.
  setInterval(() => {
    // Decrease the opacity of the element by 0.1.
    div.style.opacity -= 0.1;

    // If the opacity of the element reaches 0, stop the setInterval() function.
    if (div.style.opacity === 0) {
      clearInterval(interval);
      div.style.display = 'none';
    }
  }, 100); // 100 milliseconds is the time between each opacity change.
}, 3000); // 5 seconds in milliseconds