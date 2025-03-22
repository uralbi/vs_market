# FastAPI Market Platform and Video Streaming App

## **Server: AWS EC2, Ubuntu**

### **Check Website:**  
<a href="https://ai-ber.com" target="_blank">ai-ber.com</a>  

### **API Documentation:**  
<a href="https://ai-ber.com/docs#/" target="_blank">ai-ber.com/docs#/</a>  

## **Overview**
This is a high-performance **marketplace and video streaming platform** (currently video features are disabled due to Budget) built using **FastAPI**. The platform allows users to engage in e-commerce transactions, upload and monetize videos, and interact through real-time chat.

## **Features**
### **Marketplace**
- Users can **post products** and manage listings.  
- Integrated **mock payment API** for transactions.  

### **Video Streaming**
- Users with **"CREATOR" roles** can upload videos.  
- Creators can **offer videos for free or set a price**.  
- **Note:** Videos are not stored due to AWS EC2 storage limitations.  

### **Real-Time Chat**
- Users can communicate via **WebSockets-based chat**.  

## **Technology Stack**
- **Backend:** FastAPI (Python)  
- **Database:** PostgreSQL  
- **Authentication:** JWT-based authentication  
- **Asynchronous Processing:** Celery + Redis  [Comming: Kafka, installed and producer is ready]
- **WebSockets:** Django Channels for real-time chat  
- **Deployment:** AWS EC2 (Ubuntu)  

## **Installation and Setup**
### **1. Clone the Repository**
```sh
git clone https://github.com/uralbi/vs_market.git
pip install poetry
poetry install
