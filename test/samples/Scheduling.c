#include <stdio.h>
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "semphr.h"

#define TIME_QUANTUM 1000  // 1000ms converted to ticks
SemaphoreHandle_t semaphore;
typedef struct {
    char *taskName;
    int totalRuntime;
    int remainingTime;
    int ledNum;
    bool needsRestart; //1 means yes
    
} TaskParameters;
int numOfProcs = 4;
// Task function prototype
void vTaskCode(void *pvParameters);

// Define task run times
TaskParameters tasks[] = {
    {"Task 1", 2500, 2500, 3, true},
    {"Task 2", 3500, 3500, 7, true},
    {"Task 3", 1500, 1500, 11, true},
    {"Task 4", 2000, 2000, 15, true}
};

int main(void) {
    // Initialize GPIO for each task/LED once
    stdio_init_all();
    for (int i = 0; i < sizeof(tasks)/sizeof(tasks[0]); i++) {
        gpio_init(tasks[i].ledNum);
        gpio_set_dir(tasks[i].ledNum, GPIO_OUT);
    }
    // Create the semaphore before starting tasks
    semaphore = xSemaphoreCreateBinary();
    xSemaphoreGive(semaphore); // Give the semaphore to allow the first task to start

    // Create tasks
    for (int i = 0; i < sizeof(tasks)/sizeof(tasks[0]); i++) {
        xTaskCreate(vTaskCode, tasks[i].taskName, 1000, (void *)&tasks[i], 1, NULL);
    }

    vTaskStartScheduler();
    // Should never reach here
    for (;;) {}

    return 0;
}

// Task implementation
void vTaskCode(void *pvParameters) {
    TaskParameters *taskParams = (TaskParameters *)pvParameters;

    while (taskParams->remainingTime > 0) {
        if (xSemaphoreTake(semaphore, portMAX_DELAY) == pdTRUE) {
            gpio_put(taskParams->ledNum, 1);
            printf("%s is running, %dms remaining\n", taskParams->taskName, taskParams->remainingTime);

            int timeToRun = taskParams->remainingTime < TIME_QUANTUM ? taskParams->remainingTime : TIME_QUANTUM;
            vTaskDelay(pdMS_TO_TICKS(timeToRun));
            taskParams->remainingTime -= timeToRun;

            gpio_put(taskParams->ledNum, 0);
            xSemaphoreGive(semaphore);
            if (taskParams->remainingTime > 0) {
                vTaskDelay(pdMS_TO_TICKS(TIME_QUANTUM));
            }

            // Give the semaphore back after each run, regardless of whether the task is finished
            
        }

        // Check outside of semaphore take block to ensure that task can self-delete even if not acquiring semaphore
        if (taskParams->remainingTime <= 0) {
            printf("%s has finished execution.\n", taskParams->taskName);
            vTaskDelete(NULL);  // End this task
        }
    }
    
}
