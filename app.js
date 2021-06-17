const Discord = require("discord.js")
const {TOKEN} = require("./tok.js");


const client = new Discord.Client();

client.on("message", function (message) {
    message.channel.send("received");
});

client.login(TOKEN);

