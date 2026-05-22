delete from invitaciones_chats;
delete from solicitudes_chats;
delete from mensajes_destinatarios;
delete from mensajes;
delete from miembros_chats;
delete from chats;
delete from inscripciones_sorteos;
delete from sorteos;
delete from usuarios_socios;
delete from socios;
--delete from usuarios;

alter sequence socios_numero_socio_seq restart with 1;
commit;