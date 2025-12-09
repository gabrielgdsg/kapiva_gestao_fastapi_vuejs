# frontend/Dockerfile (production multi-stage)
# Build
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ .
RUN npm run build

# Serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# optional: custom nginx conf for SPA
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

##FROM node:latest as develop-stage
##FROM node:14-alpine as develop-stage
#FROM node:lts-alpine as develop-stage
#
#WORKDIR /app
## Copy the package.json and install dependencies
#COPY package*.json ./
##RUN npm install npm@latest
#RUN npm install --legacy-peer-deps
## Copy rest of the files
#COPY . .
## Build the project
#RUN npm run build
##___
##RUN npm install -g http-server
##EXPOSE 8080
##CMD [ "http-server", "dist" ]
##___
#FROM nginx:alpine as production-stage
#COPY --from=develop-stage /app/dist /usr/share/nginx/html
#COPY ./.nginx/nginx.conf /etc/nginx/nginx.conf
#EXPOSE 8080
#ENTRYPOINT ["nginx", "-g", "daemon off;"]
#
#
##FROM node:latest as build-stage
##WORKDIR /app
##COPY package*.json ./
##RUN npm install
##COPY ./ .
##RUN npm run build
##
##FROM nginx as production-stage
##RUN mkdir /app
##COPY --from=build-stage /app/dist /app
##COPY nginx.conf /etc/nginx/nginx.conf
#### Remove default nginx index page
##RUN rm -rf /usr/share/nginx/html/*
### Copy from the stage 1
##COPY --from=build-stage /app/dist /usr/share/nginx/html
###RUN mkdir -p /etc/nginx/sites-enabled/ \
###    && ln -s /etc/nginx/sites-available/symfony.conf /etc/nginx/sites-enabled/symfony.conf \
###    && rm /etc/nginx/conf.d/default.conf
##EXPOSE 8080
##CMD ["nginx", "-g", "daemon off;"]
#
#
#
### develop stage
##FROM node:lts-alpine as develop-stage
##WORKDIR /app
##COPY package*.json ./
##RUN npm install
###RUN npm install -g @vue/cli -g
##COPY . .
###COPY . /app
###RUN npm run serve
##
### build stage
##FROM develop-stage as build-stage
##RUN npm run build
##
### production stage
##FROM nginx:stable-alpine as production-stage
##COPY --from=build-stage /app/dist /usr/share/nginx/html
##EXPOSE 8080
##CMD ["nginx", "-g", "daemon off;"]