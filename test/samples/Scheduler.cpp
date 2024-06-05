#include <stdio.h>
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "semphr.h"
#include <stdlib.h>
#include <stdbool.h>

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

int compareTotalRuntime(const void *a, const void *b) {
    const TaskParameters *taskA = (const TaskParameters *)a;
    const TaskParameters *taskB = (const TaskParameters *)b;
    return taskA->totalRuntime - taskB->totalRuntime;
}


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
    int numTasks = sizeof(tasks) / sizeof(TaskParameters);

    // Sort the tasks array by totalRuntime
    qsort(tasks, numTasks, sizeof(TaskParameters), compareTotalRuntime);
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

    
        if (xSemaphoreTake(semaphore, portMAX_DELAY) == pdTRUE) {
            gpio_put(taskParams->ledNum, 1);
            printf("%s is running, %dms remaining\n", taskParams->taskName, taskParams->remainingTime);

            
            vTaskDelay(pdMS_TO_TICKS(taskParams->remainingTime));
            

            gpio_put(taskParams->ledNum, 0);
            xSemaphoreGive(semaphore);
           

            // Give the semaphore back after each run, regardless of whether the task is finished
            printf("%s has finished execution.\n", taskParams->taskName);
            vTaskDelete(NULL);
        }

        // Check outside of semaphore take block to ensure that task can self-delete even if not acquiring semaphore
        
    
    
}
