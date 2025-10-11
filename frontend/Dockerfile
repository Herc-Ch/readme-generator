# ---- Frontend: build with Vite then serve via Nginx ----
FROM node:20-alpine AS build
WORKDIR /frontend

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /frontend/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
