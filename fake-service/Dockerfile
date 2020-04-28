FROM node:13.13.0-slim

COPY package.json /
COPY service.js /

RUN npm install

EXPOSE 9080
CMD ["node", "/service.js", "9080"]