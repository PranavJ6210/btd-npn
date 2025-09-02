# Stage 1: Build the React application
FROM node:20-alpine as build
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve the static files with Nginx
FROM nginx:stable-alpine
# Copy the built files from the 'build' stage
COPY --from=build /usr/src/app/dist /usr/share/nginx/html
# ADD THIS LINE: Copy the custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Nginx exposes port 80 by default
EXPOSE 80
# The command to start the Nginx server
CMD ["nginx", "-g", "daemon off;"]