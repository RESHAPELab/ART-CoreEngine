document.getElementById('machine-form').addEventListener('submit', function(event) {
  const now = new Date();
  event.preventDefault();
  const machineType = document.getElementById('machine-type').value;
  const machineAge = parseInt(document.getElementById('machine-age').value);
  const replacementTime = calculateReplacementTime(machineAge, machineType);
  const resultText = `Date of Prediction: ${now.toLocaleString()}\nMachine Type: ${machineType}\nAge: ${machineAge} years\nMean time to failure: ${replacementTime} months\n\n`;
  document.getElementById('result').textContent += resultText;
  scrollToBottom();
});

// Function to scroll the textarea to the bottom
function scrollToBottom() {
    const textarea = document.getElementById('result');
    textarea.scrollTop = textarea.scrollHeight;
}

// Call scrollToBottom when the page loads to scroll to the bottom initially
window.addEventListener('load', scrollToBottom);


function calculateReplacementTime(age, machine) {

  const maxAge = 15; // assuming a machine has a lifespan of 15 years
  let remainingLife = maxAge - age;
  // Ensure remainingLife is not negative
  if (remainingLife < 0) {
    remainingLife = 0;
  }
  switch (machine) {
    case "Robotic Arm":
      return remainingLife * 10;
      break;
    case "3d Printer":
      return remainingLife * 13;
      break;
    case "CNC Machine":
      return remainingLife * 11;
      break;
    default:
      return remainingLife * 12;
  }

  // convert years to months
}
