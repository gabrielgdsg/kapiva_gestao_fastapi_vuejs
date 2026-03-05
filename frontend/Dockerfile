### --- Build Stage -----------------------------------------------------------
FROM node:18-alpine AS build
WORKDIR /app

ENV NODE_OPTIONS=--openssl-legacy-provider

# Better layer caching
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copy source
COPY . .

# Fix css-declaration-sorter incompatibility with Vue CLI 4 / Webpack 4
RUN npm install css-declaration-sorter@6.4.1 --save-dev --silent

RUN npm run build


### --- Production Stage ------------------------------------------------------
FROM nginx:alpine

# Small, fast nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Move built app
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
