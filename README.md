
<img width="332" alt="Captura de pantalla 2023-11-23 a las 19 54 13" src="https://github.com/silviluliuma/biciMAD-worker/assets/138609959/9c2deb88-1c3d-49bf-80ec-2f6641977114">

# __biciMAD-worker__

biciMAD-worker provides optimized routes between high and low-populated BiciMAD stations to address one of the platform's biggest challenges: the **redistribution** of bikes among various stations. It also captures real-time data in a Google Cloud SQL database, enabling the extraction of queries for analyzing station statuses and identifying potential issues.

## **Status**

biciMAD-worker is my python based final project for the Ironhack Data Analysis Bootcamp (Madrid 2023-2024)


## **Additional info:**

This app utilizes the biciMAD API to gather **real-time information** about biciMAD stations. It calculates the nearest low or high-populated station based on route characteristics and worker input. Using this information, it generates a **Google Maps route**, enabling workers to initiate and complete routes from their mobile phones, while also considering their **location** in real-time.

The graphical interface built with **Streamlit** enables workers to visualize a heatmap of stations requiring immediate inspection, allowing for sorted options based on this information. Additionally, users can specify whether their van is full or empty, dynamically adjusting the route order of stops accordingly. Furthermore, the interface includes two **analysis** pages (for districts and individual stations) where users can explore station and district statuses over various time periods.

<img width="587" alt="Captura de pantalla 2023-11-22 a las 19 25 08" src="https://github.com/silviluliuma/ih_datamadpt0923_project_m1/assets/138609959/39526901-5afb-4be3-a587-70e537db7455">


## **Technical information**

You can use the code of biciMAD-worker, as long as you give **autorship credits**. 

Please, clone this GitHub repository to your local machine.

![Captura de Pantalla 2024-03-14 a las 19 44 57](https://github.com/silviluliuma/biciMAD-worker/assets/138609959/e5d91d56-6646-4093-8d9e-dc6312ff5c2a)


## **Inspiration**

This project addresses the frequent complaints from biciMAD users concerning the **uneven distribution** of bikes among the stations. Throughout the workday, stations near business areas tend to become completely full due to people cycling to work, while stations in residential areas are left empty. This initiative is not only an attempt to resolve user issues but also **aims to enhance the working conditions for the employees involved**. Moreover, the data-driven analysis facilitates biciMAD in **identifying and addressing potential issues** that could impact user experience, ensuring a smoother overall service.

![workergif](https://github.com/silviluliuma/biciMAD-worker/assets/138609959/2e78b1ff-e210-4ff5-8654-d8eb1033d25d)


## **Things to improve**

In the future, the project will need to consider the **current capacity of the van**. If the van is entirely empty, the app should exclusively search for high-populated stations. If the van has bikes but still has space, the app could search for both high and low-populated stations. However, if the van is completely full, the app should focus solely on low-populated stations. The status of the van should be updated with every interaction, contributing to the continuous optimization of the route.

Also, it would be nice to use the spectacular **VROOM project** (https://github.com/VROOM-Project/vroom), which has an awesome optimization route system that allows pickups and deliveries and takes into account the time used by each worker to complete their tasks. This would offer a whole new set of possibilities.

## **Contact**

You can contact me here: valeromsilvia@gmail.com

![tumblr_otvsbuaaRF1vha0yxo5_r1_250](https://github.com/silviluliuma/ih_datamadpt0923_project_m1/assets/138609959/f597f7de-0741-4079-a9ac-a94b92359e8a)
