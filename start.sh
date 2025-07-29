#!/bin/bash

# Clear the problematic STREAMLIT_SERVER_PORT environment variable
unset STREAMLIT_SERVER_PORT

# Start Streamlit
exec streamlit run main.py 