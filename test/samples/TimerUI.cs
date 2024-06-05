using UnityEngine;
using UnityEngine.UI;

public class TimerUI : MonoBehaviour
{
    public float totalTime = 120f; // Total time in seconds
    private float currentTime; // Current time remaining

    private Text timerText;

    void Start()
    {
        // Get reference to the Text component
        timerText = GetComponent<Text>();
        
        // Initialize current time to total time
        currentTime = totalTime;

        // Start the timer coroutine
        StartCoroutine(UpdateTimer());
    }

    IEnumerator UpdateTimer()
    {
        while (currentTime > 0)
        {
            // Update current time
            currentTime -= Time.deltaTime;

            // Format time as minutes:seconds
            string minutes = Mathf.Floor(currentTime / 60).ToString("00");
            string seconds = Mathf.Floor(currentTime % 60).ToString("00");

            // Update timer text
            timerText.text = "Time: " + minutes + ":" + seconds;

            yield return null;
        }

        // If the timer reaches zero, display "Time's up!"
        timerText.text = "Time's up!";
    }
}

